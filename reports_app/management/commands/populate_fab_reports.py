from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncQuarter, TruncYear
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from fablist_app.models import FabricationListModel
from organization_app.models import OrganizationModel
from reports_app.models import FabricationReportDaily, FabricationReportMonthly, FabricationReportQuarterly, FabricationReportWeekly, FabricationReportYearly


DEPARTMENTS = ['clerk', 'shop', 'cut', 'fit', 'delivery', 'received', 'erect', 'weld', 'delivery_3p']

REPORT_CONFIGS = {
    'daily': {
        'model': 'FabricationReportDaily',
        'period_field': 'date',
        'trunc_func': TruncDay,
        'key_format': lambda x: x.date() if hasattr(x, 'date') else x.date(),  # datetime → date
    },
    'weekly': {
        'model': 'FabricationReportWeekly', 
        'period_field': 'week_start',
        'trunc_func': TruncWeek,
        'key_format': lambda x: x.date() if hasattr(x, 'date') else x.date(),
    },
    'monthly': {
        'model': 'FabricationReportMonthly',
        'period_field': 'year_month', 
        'trunc_func': TruncMonth,
        'key_format': lambda x: x.strftime('%Y-%m'),  # Works on date or datetime
    },
    'quarterly': {
        'model': 'FabricationReportQuarterly',
        'period_field': 'year_quarter',
        'trunc_func': TruncQuarter,
        'key_format': lambda x: f"{x.year}-Q{((x.month-1)//3 + 1)}",
    },
    'yearly': {
        'model': 'FabricationReportYearly',
        'period_field': 'year',
        'trunc_func': TruncYear,
        'key_format': lambda x: x.year,
    }
}

class Command(BaseCommand):
    help = 'Populate fabrication reports (daily, weekly, monthly, quarterly, yearly)'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=730, help='Days back to populate')
        parser.add_argument('--org', type=int, help='Specific organization ID')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
        parser.add_argument('--debug', action='store_true', help='Show debug info')

    def handle(self, *args, **options):
        days_back = options['days']
        org_id = options['org']
        dry_run = options['dry_run']
        debug = options.get('debug', False)
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        self.stdout.write(f"Populating reports from {start_date} to {end_date}")
        
        if org_id:
            try:
                org = OrganizationModel.objects.get(id=org_id)
                self._populate_org_reports(org, start_date, end_date, dry_run, debug)
            except ObjectDoesNotExist:
                self.stdout.write(self.style.ERROR(f"Organization {org_id} not found"))
        else:
            for org in OrganizationModel.objects.all():
                self._populate_org_reports(org, start_date, end_date, dry_run, debug)

    @transaction.atomic
    def _populate_org_reports(self, org, start_date, end_date, dry_run, debug):
        self.stdout.write(f"Processing organization {org.id}...")
        fab_qs = FabricationListModel.objects.filter(organization=org)
        
        if debug:
            self.stdout.write(f"  Found {fab_qs.count()} fabrication records")
        
        for report_type, config in REPORT_CONFIGS.items():
            self._populate_reports(fab_qs, org, start_date, end_date, config, dry_run, report_type.capitalize(), debug)

    def _populate_reports(self, fab_qs, org, start_date, end_date, config, dry_run, report_name, debug):
        all_periods = set()
        dept_data = {}
        
        total_completions = 0
        for dept in DEPARTMENTS:
            filter_kwargs = {
                f'{dept}_status': True,
                f'{dept}_completed_at__date__range': (start_date, end_date)
            }
            
            # ✅ SIMPLIFIED - No output_field needed
            completed_qs = fab_qs.filter(**filter_kwargs).annotate(
                period_trunc=config['trunc_func'](f'{dept}_completed_at')
            ).values('period_trunc').annotate(
                completed_qty=Sum('qty'),
                completed_kg=Sum('kg')
            )
            
            dept_count = completed_qs.count()
            total_completions += dept_count
            
            if debug and dept_count > 0:
                self.stdout.write(f"    {dept}: {dept_count} completions")
            
            for entry in completed_qs:
                # ✅ Robust key_format handles any datetime/date object
                period_key = config['key_format'](entry['period_trunc'])
                all_periods.add(period_key)
                
                if period_key not in dept_data:
                    dept_data[period_key] = {}
                
                dept_data[period_key][f'{dept}_completed_qty'] = entry['completed_qty'] or 0
                dept_data[period_key][f'{dept}_completed_kg'] = entry['completed_kg'] or 0.0
        
        if debug:
            self.stdout.write(f"    Total periods found: {len(all_periods)}")
        
        model_class = globals()[config['model']]
        self._save_reports(model_class, org, config['period_field'], all_periods, dept_data, dry_run, report_name)


    def _save_reports(self, model_class, org, period_field, all_periods, dept_data, dry_run, report_name):
        created_count = 0
        if not dry_run:
            for period_key in all_periods:
                data = {
                    **{f'{dept}_completed_qty': dept_data.get(period_key, {}).get(f'{dept}_completed_qty', 0) for dept in DEPARTMENTS},
                    **{f'{dept}_completed_kg': dept_data.get(period_key, {}).get(f'{dept}_completed_kg', 0.0) for dept in DEPARTMENTS},
                }
                model_class.objects.update_or_create(
                    organization=org,
                    **{period_field: period_key},
                    defaults=data
                )
                created_count += 1
        else:
            created_count = len(all_periods)
        
        self.stdout.write(f"  {report_name}: {created_count} records")


from django.contrib.auth import get_user_model
from django_solvitize.utils.GlobalFunctions import *
from django_solvitize.utils.GlobalImports import *
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
import io
import sys
from contextlib import redirect_stdout
from datetime import datetime, date, timedelta
import calendar

from reports_app.models import FabricationReportDaily, FabricationReportMonthly, FabricationReportQuarterly, FabricationReportWeekly, FabricationReportYearly
# Create your views here.


class FabKgReportAPI(ListAPIView):
    def get(self, request, *args, **kwargs):
        print("FabKgReportAPI Request: ", request.GET)
        interval = request.GET.get("interval")
        organization = request.GET.get("organization")
        interval_from = request.GET.get("interval_from")
        interval_to = request.GET.get("interval_to")
        
        required = ["interval"]
        validation_errors = ValidateRequest(required, request.GET)
        if validation_errors:
            return ResponseFunction(0, validation_errors[0]["error"], {})

        # Parse dates
        start_date = datetime.strptime(interval_from, "%Y-%m-%d").date()
        end_date = datetime.strptime(interval_to, "%Y-%m-%d").date()

        # FIXED FILTERING
        if interval == "daily":
            report_qs = FabricationReportDaily.objects.filter(
                date__range=(interval_from, interval_to),
            ).order_by('date').values()
        elif interval == "weekly":
            report_qs = FabricationReportWeekly.objects.filter(
                week_start__range=(interval_from, interval_to),
            ).order_by('week_start').values()
        elif interval == "monthly":
            # ✅ FIXED: Generate proper year_month strings
            months = self._get_month_strings(start_date, end_date)
            print("Months: ", months)
            report_qs = FabricationReportMonthly.objects.filter(
                year_month__in=months,
            ).order_by('year_month').values()
        elif interval == "quarterly":
            # ✅ FIXED: Generate proper year_quarter strings  
            quarters = self._get_quarter_strings(start_date, end_date)
            print("Quarters: ", quarters)
            # print(FabricationReportQuarterly.objects.all().order_by('year_quarter').values())
            report_qs = (
                FabricationReportQuarterly.objects.
                filter(year_quarter__in=quarters,).
                # all().
                order_by('year_quarter').values())
        elif interval == "yearly":
            years = self._get_year_range(start_date, end_date)
            report_qs = FabricationReportYearly.objects.filter(
                year__in=years,
            ).order_by('year').values()
        else:
            return ResponseFunction(0, "Invalid interval", {})

        data = self._fill_missing_periods(report_qs, interval, interval_from, interval_to)
        
        return ResponseFunction(1, "Success", {
            "interval": interval,
            "interval_from": interval_from,
            "interval_to": interval_to,
            "data": data
        })

    def _get_month_strings(self, start_date, end_date):
        """Generate ['2025-11'] from date range"""
        months = []
        current = start_date.replace(day=1)
        while current <= end_date:
            months.append(current.strftime('%Y-%m'))
            if current.month == 12:
                current = current.replace(year=current.year+1, month=1)
            else:
                current = current.replace(month=current.month+1)
        return months

    def _get_quarter_strings(self, start_date, end_date):
        """Generate ['2025-Q4'] from date range"""
        quarters = set()
        current = start_date.replace(day=1)
        while current <= end_date:
            q = ((current.month-1)//3 + 1)
            quarters.add(f"{current.year}-Q{q}")
            # Advance to next quarter start
            next_quarter_month = q * 3 + 1
            if next_quarter_month > 12:
                current = current.replace(year=current.year+1, month=1, day=1)
            else:
                current = current.replace(month=next_quarter_month, day=1)
        return list(quarters)

    def _get_year_range(self, start_date, end_date):
        """Generate [2025, 2026] from date range"""
        return list(range(start_date.year, end_date.year + 1))

    def _fill_missing_periods(self, report_qs, interval, interval_from, interval_to):
        # Convert strings to date objects
        start = datetime.strptime(interval_from, "%Y-%m-%d").date()
        end = datetime.strptime(interval_to, "%Y-%m-%d").date()

        # Build lookup from existing report rows
        period_data = {}

        for row in report_qs:
            if interval == "daily":
                period_date = row["date"]           # FabricationReportDaily
            elif interval == "weekly":
                period_date = row["week_start"]     # FabricationReportWeekly
            elif interval == "monthly":
                # If you use year_month like "2025-11"
                ym = row["year_month"]
                period_date = date(int(ym[:4]), int(ym[5:7]), 1)
            elif interval == "quarterly":
                # Parse year_quarter like "2025-Q4"
                yq = row["year_quarter"]
                year = int(yq[:4])
                quarter = int(yq[-1])
                quarter_start_month = (quarter - 1) * 3 + 1  # Q1=1, Q2=4, Q3=7, Q4=10
                period_date = date(year, quarter_start_month, 1)
            else:  # yearly
                year = row["year"]
                period_date = date(year, 1, 1)

            period_key = self._format_period_key(period_date, interval)
            # Copy everything except the key fields
            clean_row = {k: v for k, v in row.items()
                         if k not in ["date", "week_start", "year_month", "year_quarter", "year", "organization_id", "organization"]}
            period_data[period_key] = clean_row

        # Generate continuous periods
        data = []
        current = start

        if interval == "weekly":
            # align to Sunday to match TruncWeek + %U
            days_to_sunday = (6 - current.weekday()) % 7
            current = current + timedelta(days=days_to_sunday)
        elif interval == "quarterly":
            # align to quarter start (first day of first month in quarter)
            quarter = (current.month - 1) // 3 + 1
            quarter_start_month = (quarter - 1) * 3 + 1
            current = current.replace(month=quarter_start_month, day=1)
        elif interval == "monthly":
            # align to first day of month
            current = current.replace(day=1)

        while current <= end:
            if interval == "daily":
                period_key = current.strftime("%Y-%m-%d")
                current += timedelta(days=1)

            elif interval == "weekly":
                period_key = current.strftime("%b WEEK_%U")
                current += timedelta(weeks=1)

            elif interval == "monthly":
                period_key = current.strftime("%b %Y")
                # move to first day of next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=current.month + 1, day=1)

            elif interval == "quarterly":
                # Calculate quarter and generate period key
                quarter = (current.month - 1) // 3 + 1
                quarter_start_month = (quarter - 1) * 3 + 1  # 10 for Q4, 1 for Q1, etc.
                display_month = date(current.year, quarter_start_month, 1).strftime('%b')
                period_key = f"{display_month} Q{quarter} {current.year}"
                
                # Advance to next quarter start
                next_quarter_month = quarter * 3 + 1
                if next_quarter_month > 12:
                    current = current.replace(year=current.year + 1, month=1, day=1)
                else:
                    current = current.replace(month=next_quarter_month, day=1)

            # elif interval == "quarterly":
            #     quarter = (current.month - 1) // 3 + 1
            #     period_key = f"{current.strftime('%b')} Q{quarter} {current.year}"
            #     print("quarter: ", quarter)
            #     print("period_key: ", period_key)
            #     # move to first month of next quarter
            #     if quarter == 4:
            #         current = current.replace(year=current.year + 1, month=1, day=1)
            #     else:
            #         current = current.replace(month=quarter * 3 + 1, day=1)
            #     print("current: ", current)
            else:  # yearly
                period_key = current.strftime("%Y")
                current = current.replace(year=current.year + 1, month=1, day=1)

            # default values: all metrics 0
            row = period_data.get(period_key)
            if not row:
                row = {
                    "total_qty": 0,
                    "total_kg": 0.0,
                    "clerk_completed_qty": 0,
                    "clerk_completed_kg": 0.0,
                    "shop_completed_qty": 0,
                    "shop_completed_kg": 0.0,
                    "cut_completed_qty": 0,
                    "cut_completed_kg": 0.0,
                    "fit_completed_qty": 0,
                    "fit_completed_kg": 0.0,
                    "delivery_completed_qty": 0,
                    "delivery_completed_kg": 0.0,
                    "received_completed_qty": 0,
                    "received_completed_kg": 0.0,
                    "erect_completed_qty": 0,
                    "erect_completed_kg": 0.0,
                    "weld_completed_qty": 0,
                    "weld_completed_kg": 0.0,
                    "delivery_3p_completed_qty": 0,
                    "delivery_3p_completed_kg": 0.0,
                }

            data.append({period_key: row})

        return data

    def _format_period_key(self, period, interval):
        if interval == "daily":
            return period.strftime("%Y-%m-%d")
        elif interval == "weekly":
            return period.strftime("%b WEEK_%U")   # matches TruncWeek + %U
        elif interval == "monthly":
            return period.strftime("%b %Y")
        # elif interval == "quarterly":
        #     quarter = (period.month - 1) // 3 + 1
        #     val = f"{period.strftime('%b')} Q{quarter} {period.year}"
        #     print("val: ", val)
        #     val2 = f"Q{quarter} {period.year}"
        #     print("val2: ", val2)
        #     return val
        elif interval == "quarterly":
            quarter = (period.month - 1) // 3 + 1
            quarter_start_month = (quarter - 1) * 3 + 1
            display_month = date(period.year, quarter_start_month, 1).strftime('%b')
            return f"{display_month} Q{quarter} {period.year}"  # "Oct Q4 2025"

        else:
            return period.strftime("%Y")
        




class PopulateReportsAPI(APIView):
    def get(self, request):
        # Parse query params
        days = request.GET.get('days', 365)  # Default 1 years
        org_id = request.GET.get('org')      # Optional organization ID
        dry_run = request.GET.get('dry_run', 'false').lower() == 'true'
        debug = request.GET.get('debug', 'false').lower() == 'true'
        
        # Validate days
        try:
            days = int(days)
            if days < 1 or days > 3650:  # Max 10 years
                return Response({"error": "Days must be 1-3650"}, status=400)
        except ValueError:
            return Response({"error": "Invalid days parameter"}, status=400)
        
        # Capture command output
        output = io.StringIO()
        
        # Build management command args
        cmd_args = []
        if org_id:
            cmd_args.extend(['--org', str(org_id)])
        if dry_run:
            cmd_args.append('--dry-run')
        if debug:
            cmd_args.append('--debug')
        
        try:
            # Redirect stdout to capture output
            with redirect_stdout(output):
                call_command('populate_fab_reports', 
                           '--days', str(days), 
                           *cmd_args)
            
            result = {
                "days_back": days,
                "organization_id": org_id or "all",
                "dry_run": dry_run,
                "debug": debug,
                "output": output.getvalue().strip()
            }
            return ResponseFunction(1, "Successfully populated reports", result)
            
        except Exception as e:
            result = {
                "days_back": days,
                "organization_id": org_id or "all"
            }
        
            return ResponseFunction(0, f"Failed to populate reports with error {str(e)}", result)

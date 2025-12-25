from django.db import models

from core_app.models import AbstractDate

# Create your models here.

class FabricationReportBase(AbstractDate,models.Model):
    organization = models.ForeignKey('organization_app.OrganizationModel', on_delete=models.PROTECT)
    class Meta:
        abstract = True

class FabricationReportDaily(FabricationReportBase):
    date = models.DateField(db_index=True)
    
    # Each department completion
    clerk_completed_qty = models.IntegerField(default=0)
    clerk_completed_kg = models.FloatField(default=0)

    shop_completed_qty = models.IntegerField(default=0)
    shop_completed_kg = models.FloatField(default=0)

    cut_completed_qty = models.IntegerField(default=0)
    cut_completed_kg = models.FloatField(default=0)

    fit_completed_qty = models.IntegerField(default=0)
    fit_completed_kg = models.FloatField(default=0)

    delivery_completed_qty = models.IntegerField(default=0)
    delivery_completed_kg = models.FloatField(default=0)

    received_completed_qty = models.IntegerField(default=0)
    received_completed_kg = models.FloatField(default=0)

    erect_completed_qty = models.IntegerField(default=0)
    erect_completed_kg = models.FloatField(default=0)

    weld_completed_qty = models.IntegerField(default=0)
    weld_completed_kg = models.FloatField(default=0)

    delivery_3p_completed_qty = models.IntegerField(default=0)
    delivery_3p_completed_kg = models.FloatField(default=0)
    
    class Meta(FabricationReportBase.Meta):
        unique_together = ['date', 'organization']

class FabricationReportWeekly(FabricationReportBase):
    week_start = models.DateField(db_index=True)
    # Same fields as daily...
    # (copy all *_completed_qty/kg fields)
        
    # Each department completion
    clerk_completed_qty = models.IntegerField(default=0)
    clerk_completed_kg = models.FloatField(default=0)

    shop_completed_qty = models.IntegerField(default=0)
    shop_completed_kg = models.FloatField(default=0)

    cut_completed_qty = models.IntegerField(default=0)
    cut_completed_kg = models.FloatField(default=0)

    fit_completed_qty = models.IntegerField(default=0)
    fit_completed_kg = models.FloatField(default=0)

    delivery_completed_qty = models.IntegerField(default=0)
    delivery_completed_kg = models.FloatField(default=0)

    received_completed_qty = models.IntegerField(default=0)
    received_completed_kg = models.FloatField(default=0)

    erect_completed_qty = models.IntegerField(default=0)
    erect_completed_kg = models.FloatField(default=0)

    weld_completed_qty = models.IntegerField(default=0)
    weld_completed_kg = models.FloatField(default=0)
    
    delivery_3p_completed_qty = models.IntegerField(default=0)
    delivery_3p_completed_kg = models.FloatField(default=0)
    
    class Meta(FabricationReportBase.Meta):
        unique_together = ['week_start', 'organization']


class FabricationReportMonthly(FabricationReportBase):
    year_month = models.CharField(max_length=7, db_index=True)  # "2025-11"
    # Same fields...

        
    # Each department completion
    clerk_completed_qty = models.IntegerField(default=0)
    clerk_completed_kg = models.FloatField(default=0)

    shop_completed_qty = models.IntegerField(default=0)
    shop_completed_kg = models.FloatField(default=0)

    cut_completed_qty = models.IntegerField(default=0)
    cut_completed_kg = models.FloatField(default=0)

    fit_completed_qty = models.IntegerField(default=0)
    fit_completed_kg = models.FloatField(default=0)

    delivery_completed_qty = models.IntegerField(default=0)
    delivery_completed_kg = models.FloatField(default=0)

    received_completed_qty = models.IntegerField(default=0)
    received_completed_kg = models.FloatField(default=0)

    erect_completed_qty = models.IntegerField(default=0)
    erect_completed_kg = models.FloatField(default=0)

    weld_completed_qty = models.IntegerField(default=0)
    weld_completed_kg = models.FloatField(default=0)
    
    delivery_3p_completed_qty = models.IntegerField(default=0)
    delivery_3p_completed_kg = models.FloatField(default=0)
    
    class Meta(FabricationReportBase.Meta):
        unique_together = ['year_month', 'organization']


class FabricationReportQuarterly(FabricationReportBase):
    year_quarter = models.CharField(max_length=7, db_index=True)  # "2025-Q4"
    # Same fields...
        
    # Each department completion
    clerk_completed_qty = models.IntegerField(default=0)
    clerk_completed_kg = models.FloatField(default=0)

    shop_completed_qty = models.IntegerField(default=0)
    shop_completed_kg = models.FloatField(default=0)

    cut_completed_qty = models.IntegerField(default=0)
    cut_completed_kg = models.FloatField(default=0)

    fit_completed_qty = models.IntegerField(default=0)
    fit_completed_kg = models.FloatField(default=0)

    delivery_completed_qty = models.IntegerField(default=0)
    delivery_completed_kg = models.FloatField(default=0)

    received_completed_qty = models.IntegerField(default=0)
    received_completed_kg = models.FloatField(default=0)

    erect_completed_qty = models.IntegerField(default=0)
    erect_completed_kg = models.FloatField(default=0)

    weld_completed_qty = models.IntegerField(default=0)
    weld_completed_kg = models.FloatField(default=0)
    
    delivery_3p_completed_qty = models.IntegerField(default=0)
    delivery_3p_completed_kg = models.FloatField(default=0)
    
    class Meta(FabricationReportBase.Meta):
        unique_together = ['year_quarter', 'organization']


class FabricationReportYearly(FabricationReportBase):
    year = models.IntegerField(db_index=True)
    # Same fields...
        
    # Each department completion
    clerk_completed_qty = models.IntegerField(default=0)
    clerk_completed_kg = models.FloatField(default=0)

    shop_completed_qty = models.IntegerField(default=0)
    shop_completed_kg = models.FloatField(default=0)

    cut_completed_qty = models.IntegerField(default=0)
    cut_completed_kg = models.FloatField(default=0)

    fit_completed_qty = models.IntegerField(default=0)
    fit_completed_kg = models.FloatField(default=0)

    delivery_completed_qty = models.IntegerField(default=0)
    delivery_completed_kg = models.FloatField(default=0)

    received_completed_qty = models.IntegerField(default=0)
    received_completed_kg = models.FloatField(default=0)

    erect_completed_qty = models.IntegerField(default=0)
    erect_completed_kg = models.FloatField(default=0)

    weld_completed_qty = models.IntegerField(default=0)
    weld_completed_kg = models.FloatField(default=0)
    
    delivery_3p_completed_qty = models.IntegerField(default=0)
    delivery_3p_completed_kg = models.FloatField(default=0)
    
    class Meta(FabricationReportBase.Meta):
        unique_together = ['year', 'organization']


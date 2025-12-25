from django.contrib import admin

from reports_app.models import FabricationReportDaily, FabricationReportMonthly, FabricationReportQuarterly, FabricationReportWeekly, FabricationReportYearly

common_list_display = ['clerk_completed_qty', 'clerk_completed_kg']
# Register your models here.
class FabricationReportDailyAdmin(admin.ModelAdmin):
    list_display = ['id', 'date'] + common_list_display

class FabricationReportWeeklyAdmin(admin.ModelAdmin):
    list_display = ['id', 'week_start'] + common_list_display

class FabricationReportMonthlyAdmin(admin.ModelAdmin):
    list_display = ['id', 'year_month'] + common_list_display

class FabricationReportQuarterlyAdmin(admin.ModelAdmin):
    list_display = ['id', 'year_quarter'] + common_list_display

class FabricationReportYearlyAdmin(admin.ModelAdmin):
    list_display = ['id', 'year'] + common_list_display
    

admin.site.register(FabricationReportDaily, FabricationReportDailyAdmin)
admin.site.register(FabricationReportWeekly, FabricationReportWeeklyAdmin)
admin.site.register(FabricationReportMonthly, FabricationReportMonthlyAdmin)
admin.site.register(FabricationReportQuarterly, FabricationReportQuarterlyAdmin)
admin.site.register(FabricationReportYearly, FabricationReportYearlyAdmin)
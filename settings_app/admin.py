from django.contrib import admin

from settings_app.models import SettingsModel

# Register your models here.

class SettingsAdmin(admin.ModelAdmin):
    list_display = ('field_name', 'data_type', 'value', 'description', 'is_active')
    search_fields = ('field_name', 'data_type', 'value', 'description')
    
admin.site.register(SettingsModel, SettingsAdmin)
    
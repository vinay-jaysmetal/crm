from django.contrib import admin

from organization_app.models import OrganizationModel

# Register your models here.

class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)
    ordering = ('-created_at',)
    
admin.site.register(OrganizationModel, OrganizationAdmin)
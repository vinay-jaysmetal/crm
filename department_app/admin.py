from django.contrib import admin

from department_app.models import DepartmentModel

# Register your models here.
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)
    
    
admin.site.register(DepartmentModel, DepartmentAdmin)
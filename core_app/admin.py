from django.contrib import admin

# Register your models here.
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active', )
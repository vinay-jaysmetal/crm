from django.contrib import admin

from fablist_app.models import FabricationListModel, FabricationStatusModel

# Register your models here.

class FabricationStatusModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'fabrication_item', 'fabrication_item__organization', 'user','user_first_name', 'department', 'is_completed', )
    search_fields = ('fabrication_item__name', 'user__first_name', 'department__name')
    list_filter = ('department','fabrication_item__organization', 'is_completed')
    
    readonly_fields = ('user_id_value', 'user_first_name', 'user_mobile', 'user_email', 'created_at', 'updated_at')
    
    raw_id_fields = ('fabrication_item', 'user', 'department')

    def user_first_name(self, obj):
        return obj.user.first_name if obj.user else "N/A"

class FabricationStatusInline(admin.TabularInline):  # You can also use admin.StackedInline
    model = FabricationStatusModel
    extra = 0  # How many empty forms to display
    fields = ( 'department', 'is_completed', 'completed_at')
    
    # side navigation name
    verbose_name = 'Fabrication User Status'
    plural = 'Fabrication User Status'
    
    show_change_link = True


class FabricationListAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'qty', 'kg', 'total_kg', 'organization', 'project')
    search_fields = ('name',)
    list_editable = ('qty', 'kg','organization')
    list_filter = ('organization',)
    raw_id_fields = ('organization','project')
    
    inlines = [FabricationStatusInline,]                                   
    
admin.site.register(FabricationListModel, FabricationListAdmin)
admin.site.register(FabricationStatusModel, FabricationStatusModelAdmin)
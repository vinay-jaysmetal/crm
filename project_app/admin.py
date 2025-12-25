from django.contrib import admin

from fablist_app.models import FabricationListModel
from project_app.models import ProjectGalleryModel, ProjectModel, ProjectUserModel, ProjectContact, ProjectTask


class FabricationListInline(admin.TabularInline):  # You can also use admin.StackedInline
    model = FabricationListModel
    extra = 0  # How many empty forms to display
    fields = ('name', 'qty', 'kg')
    show_change_link = True
    
class ProjectGalleryModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'project')
    list_filter = ('organise_type',)
    raw_id_fields = ('project',)
    
# Register your models here.
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'organization', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)
    list_editable = ('organization',)
    
    
    inlines = [FabricationListInline]


class ProjectUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user',
                    # 'department', 
                    'project','organization', 'is_active')
    # search_fields = ('user__username', 'project__name')
    list_filter = ('is_active',)
    raw_id_fields = ('user', 'project')


class ProjectContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'contact_name', 'contact_email',
                    'project','contact_role', 'is_active')
    # search_fields = ('user__username', 'project__name')
    list_filter = ('is_active',)
    raw_id_fields = ( 'project',)


class ProjectTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_type', 'area', 'project',
                    'completed_by', 'is_completed', 'is_active')
    # search_fields = ('user__username', 'project__name')
    list_filter = ('is_active',)
    raw_id_fields = ( 'project', 'completed_by')
    
admin.site.register(ProjectModel,ProjectAdmin)
admin.site.register(ProjectUserModel, ProjectUserAdmin) 
admin.site.register(ProjectContact, ProjectContactAdmin) 
admin.site.register(ProjectTask, ProjectTaskAdmin) 
admin.site.register(ProjectGalleryModel, ProjectGalleryModelAdmin)

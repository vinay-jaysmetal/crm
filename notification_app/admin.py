from django.contrib import admin

from notification_app.models import NotificationModel, NotificationUserModel

# Register your models here.
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_active')
    search_fields = ('title',)
    list_filter = ('is_active',)
    
    
class NotificationUserAdmin(admin.ModelAdmin):
    
    list_display = ('id', 'user', 'notification', 'is_seen', 'is_read', 'delivered_at')
    list_filter = ('is_seen','is_read',)
    raw_id_fields = ('user', 'notification')
    
    
    
admin.site.register(NotificationModel, NotificationAdmin)
admin.site.register(NotificationUserModel, NotificationUserAdmin)
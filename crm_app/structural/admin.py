from django.contrib import admin
from .models import (
    StructuralCustomer,
    StructuralContact,
    StructuralNote,
    StructuralNotification,
    StructuralProject,
    StructuralReminder,
    StructuralCalendarActivity,
    StructuralNotification
)

# ----------------------------
# Structural Company Admin
# ----------------------------
class StructuralCustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'company_type', 'added_by', 'created_at')
    search_fields = ('company_name', 'phone', 'email')
    list_filter = ('company_type', 'lead_status', 'project_status')
    ordering = ('-created_at',)

admin.site.register(StructuralCustomer, StructuralCustomerAdmin)


# ----------------------------
# Structural Contact Admin
# ----------------------------
class StructuralContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'role', 'company', 'phone', 'email')
    search_fields = ('name', 'phone', 'email')
    list_filter = ('role',)
    ordering = ('-id',)

admin.site.register(StructuralContact, StructuralContactAdmin)


# ----------------------------
# Structural Note Admin
# ----------------------------
class StructuralNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'created_by', 'created_at')
    search_fields = ('note',)
    ordering = ('-created_at',)

admin.site.register(StructuralNote, StructuralNoteAdmin)


# ----------------------------
# Structural Project Admin
# ----------------------------
class StructuralProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company', 'status')
    search_fields = ('name', 'company__name')
    list_filter = ('status',)
    ordering = ('-id',)

admin.site.register(StructuralProject, StructuralProjectAdmin)


# ----------------------------
# Structural Reminder Admin
# ----------------------------
class StructuralReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'frequency', 'reminder_date', 'completed')
    list_filter = ('frequency', 'completed')
    ordering = ('-reminder_date',)

admin.site.register(StructuralReminder, StructuralReminderAdmin)


# ----------------------------
# Structural Calendar Activity Admin
# ----------------------------
class StructuralCalendarActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'activity_date', 'company', 'created_at')
    search_fields = ('description',)
    ordering = ('-activity_date',)

admin.site.register(StructuralCalendarActivity, StructuralCalendarActivityAdmin)


class StructuralNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'sales_person', 'company', 'reminder', 'created_at')
    search_fields = ('company__company_name',)
    ordering = ('-created_at',)

admin.site.register(StructuralNotification, StructuralNotificationAdmin)    
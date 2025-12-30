from django.contrib import admin
from .models import (
    StructuralCustomer,
    StructuralContact,
    StructuralNote,
    StructuralProject,
    StructuralReminder,
    StructuralCalendarActivity,
    StructuralNotification,
)


# ----------------------------
# Structural Customer Admin
# ----------------------------
@admin.register(StructuralCustomer)
class StructuralCustomerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'company_name',
        'category',
        'lead_status',
        'project_status',
        'added_by',
        'created_at',
    )
    search_fields = ('company_name', 'phone', 'email')
    list_filter = ('category', 'lead_status', 'project_status')
    ordering = ('-created_at',)


# ----------------------------
# Structural Contact Admin
# ----------------------------
@admin.register(StructuralContact)
class StructuralContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'role', 'company', 'phone', 'email')
    search_fields = ('name', 'phone', 'email')
    ordering = ('-id',)


# ----------------------------
# Structural Note Admin
# ----------------------------
@admin.register(StructuralNote)
class StructuralNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'created_by', 'created_at')
    search_fields = ('note',)
    ordering = ('-created_at',)


# ----------------------------
# Structural Project Admin
# ----------------------------
@admin.register(StructuralProject)
class StructuralProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company', 'status')
    search_fields = ('name', 'company__company_name')
    list_filter = ('status',)
    ordering = ('-id',)


# ----------------------------
# Structural Reminder Admin
# ----------------------------
@admin.register(StructuralReminder)
class StructuralReminderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'company',
        'project',
        'assigned_to',
        'frequency',
        'reminder_date',
        'status',
        'completed_at',
    )

    list_filter = (
        'status',
        'frequency',
        'assigned_to',
    )

    search_fields = (
        'company__company_name',
        'assigned_to__username',
    )

    ordering = ('-reminder_date',)

    readonly_fields = (
        'completed_at',
        'created_at',
    )


# ----------------------------
# Structural Calendar Activity Admin
# ----------------------------
@admin.register(StructuralCalendarActivity)
class StructuralCalendarActivityAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'activity_date',
        'company',
        'user',
        'related_reminder',
        'created_at',
    )
    search_fields = ('description',)
    ordering = ('-activity_date',)


# ----------------------------
# Structural Notification Admin
# ----------------------------
@admin.register(StructuralNotification)
class StructuralNotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sales_person',
        'company',
        'reminder',
        'read',
        'created_at',
    )
    list_filter = ('read',)
    search_fields = ('company__company_name',)
    ordering = ('-created_at',)

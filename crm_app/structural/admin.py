from django.contrib import admin
from .models import (
    StructuralCompany,
    StructuralContact,
    StructuralNote,
    StructuralProject,
    StructuralReminder,
    StructuralCalendarActivity
)

# ----------------------------
# Structural Company Admin
# ----------------------------
class StructuralCompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company_type', 'added_by', 'created_at')
    search_fields = ('name', 'phone', 'email')
    list_filter = ('company_type', 'lead_status', 'project_status')
    ordering = ('-created_at',)

admin.site.register(StructuralCompany, StructuralCompanyAdmin)


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

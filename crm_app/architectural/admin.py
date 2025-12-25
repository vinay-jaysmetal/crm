from django.contrib import admin
from .models import (
    ArchitecturalCompany,
    ArchitecturalContact,
    ArchitecturalNote,
    ArchitecturalProject,
    ArchitecturalReminder,
    ArchitecturalCalendarActivity
)

# ----------------------------
# Architectural Company Admin
# ----------------------------
class ArchitecturalCompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company_type', 'added_by', 'created_at')
    search_fields = ('name', 'phone', 'email')
    list_filter = ('company_type', 'lead_status', 'project_status')
    ordering = ('-created_at',)

admin.site.register(ArchitecturalCompany, ArchitecturalCompanyAdmin)


# ----------------------------
# Architectural Contact Admin
# ----------------------------
class ArchitecturalContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'role', 'company', 'phone', 'email')
    search_fields = ('name', 'phone', 'email')
    list_filter = ('role',)
    ordering = ('-id',)

admin.site.register(ArchitecturalContact, ArchitecturalContactAdmin)


# ----------------------------
# Architectural Note Admin
# ----------------------------
class ArchitecturalNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'created_by', 'created_at')
    search_fields = ('note',)
    ordering = ('-created_at',)

admin.site.register(ArchitecturalNote, ArchitecturalNoteAdmin)


# ----------------------------
# Architectural Project Admin
# ----------------------------
class ArchitecturalProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company', 'status')
    search_fields = ('name', 'company__name')
    list_filter = ('status',)
    ordering = ('-id',)

admin.site.register(ArchitecturalProject, ArchitecturalProjectAdmin)


# ----------------------------
# Architectural Reminder Admin
# ----------------------------
class ArchitecturalReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'frequency', 'reminder_date', 'completed')
    list_filter = ('frequency', 'completed')
    ordering = ('-reminder_date',)

admin.site.register(ArchitecturalReminder, ArchitecturalReminderAdmin)



# ----------------------------
# Architectural Calendar Activity Admin
# ----------------------------
class ArchitecturalCalendarActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'activity_date', 'company', 'created_at')
    search_fields = ('description',)
    ordering = ('-activity_date',)

admin.site.register(ArchitecturalCalendarActivity, ArchitecturalCalendarActivityAdmin)

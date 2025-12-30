from datetime import timedelta
from dateutil.relativedelta import relativedelta
from .models import StructuralReminder
from .models import StructuralReminder, StructuralNotification


def create_next_recurring_reminder(reminder):
    """
    Auto-create next recurring reminder after completion
    """

    if reminder.frequency == "Weekly":
        next_date = reminder.reminder_date + timedelta(days=7)

    elif reminder.frequency == "Monthly":
        next_date = reminder.reminder_date + relativedelta(months=1)

    elif reminder.frequency == "Yearly":
        next_date = reminder.reminder_date + relativedelta(years=1)

    else:
        # Custom / None → no recurrence
        return None

    return StructuralReminder.objects.create(
        company=reminder.company,
        project=getattr(reminder, "project", None),
        assigned_to=reminder.assigned_to,
        reminder_date=next_date,
        frequency=reminder.frequency,
        status="Scheduled"   # 🔑 IMPORTANT
    )

def process_today_reminders():
    """
    Move today's scheduled reminders to pending
    and create notifications
    """
    today = timezone.now().date()

    reminders = StructuralReminder.objects.filter(
        reminder_date=today,
        status='Scheduled'
    )

    for r in reminders:
        r.status = 'Pending'
        r.save(update_fields=["status"])

        # Avoid duplicate notifications
        if not StructuralNotification.objects.filter(reminder=r).exists():
            StructuralNotification.objects.create(
                sales_person=r.assigned_to,
                company=r.company,
                reminder=r,
                title="Reminder Due Today",
                message=f"Follow-up for {r.company.company_name}"
            )
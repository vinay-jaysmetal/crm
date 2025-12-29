# utils.py
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from .models import StructuralReminder

def create_next_reminder(reminder):
    if reminder.frequency == "Weekly":
        next_date = reminder.reminder_date + timedelta(days=7)
    elif reminder.frequency == "Monthly":
        next_date = reminder.reminder_date + relativedelta(months=1)
    elif reminder.frequency == "Yearly":
        next_date = reminder.reminder_date + relativedelta(years=1)
    else:
        return None

    return StructuralReminder.objects.create(
        company=reminder.company,
        assigned_to=reminder.assigned_to,
        reminder_date=next_date,
        frequency=reminder.frequency,
        note=reminder.note
    )

from django.db import models
from django.conf import settings

# ----------------------------
# Company / Customer Account
# ----------------------------
class StructuralCustomer(models.Model):
    CATEGORY_CHOICES = [
        ('GC', 'GC'),
        ('Builder', 'Builder'),
        ('Architect', 'Architect'),
    ]
    COMPANY_TYPE_CHOICES = [
        ('Existing', 'Existing'),
        ('Potential', 'Potential'),
    ]
    LEAD_STATUS_CHOICES = [
        ('Hot', 'Hot'),
        ('Warm', 'Warm'),
        ('Cold', 'Cold'),
    ]
    PROJECT_STATUS_CHOICES = [
        ('Hot', 'Hot'),
        ('Warm', 'Warm'),
        ('Cold', 'Cold'),
    ]

    # Company Info
    company_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    address = models.TextField(blank=True, null=True)

    # Type & Categories
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES)
    existing_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)
    potential_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)

    # Status
    lead_status = models.CharField(max_length=10, choices=LEAD_STATUS_CHOICES, blank=True, null=True)
    project_status = models.CharField(max_length=10, choices=PROJECT_STATUS_CHOICES, blank=True, null=True)

    # Ownership
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name="structural_companies")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name


# ----------------------------
# Multiple Contacts per Company
# ----------------------------
class StructuralContact(models.Model):
    company = models.ForeignKey(StructuralCustomer, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return f"{self.name} ({self.company.company_name})"


# ----------------------------
# Notes per Company
# ----------------------------
class StructuralNote(models.Model):
    company = models.ForeignKey(StructuralCustomer, on_delete=models.CASCADE, related_name="notes")
    note = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ----------------------------
# Projects per Company
# ----------------------------
class StructuralProject(models.Model):
    STATUS_CHOICES = [
        ('Hot', 'Hot'),
        ('Warm', 'Warm'),
        ('Cold', 'Cold'),
    ]

    company = models.ForeignKey(StructuralCustomer, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Hot')

    def __str__(self):
        return f"{self.name} ({self.company.company_name})"


# ----------------------------
# Reminders per Company
# ----------------------------
class StructuralReminder(models.Model):
    FREQUENCY_CHOICES = [
        ('None', 'None'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Yearly', 'Yearly'),
        ('Custom', 'Custom'),
    ]

    company = models.ForeignKey(StructuralCustomer, on_delete=models.CASCADE, related_name="reminders")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders")
    reminder_date = models.DateField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='None')
    note = models.TextField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Reminder for {self.company.company_name} on {self.reminder_date}"


# ----------------------------
# Calendar Activities per Company
# ----------------------------
class StructuralCalendarActivity(models.Model):
    company = models.ForeignKey(StructuralCustomer, on_delete=models.CASCADE, related_name="calendar_activities")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    related_reminder = models.ForeignKey(
        StructuralReminder, on_delete=models.SET_NULL, null=True, blank=True
    )
    title = models.CharField(max_length=255)
    activity_date = models.DateField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.activity_date} - {self.company.company_name}"

class StructuralNotification(models.Model):
    sales_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    company = models.ForeignKey(
        StructuralCustomer,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    reminder = models.ForeignKey(
        StructuralReminder,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=255)
    message = models.TextField()   # reminder note used as message
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.company.company_name}"

from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Lead(models.Model):
    LEAD_STATUS_CHOICES = [
        ('Hot', 'Hot'),
        ('Warm', 'Warm'),
        ('Cold', 'Cold'),
    ]

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    added_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="leads"
    )

    # structural_company = models.ForeignKey(
    #     'structural.StructuralCompany',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="leads"
    # )
    # architectural_company = models.ForeignKey(
    #     'architectural.ArchitecturalCompany',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="leads"
    # )

    status = models.CharField(max_length=10, choices=LEAD_STATUS_CHOICES, default='Hot')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.status}"

from django.db import models

from core_app.models import AbstractDate

# Create your models here.
class OrganizationModel(AbstractDate, models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
from django.db import models

# Create your models here.
DATA_TYPE = (
    ("ARRAY", "ARRAY"),
    ("NUMBER", "NUMBER"),
    ("TEXT", "TEXT"),
    ("BOOLEAN", "BOOLEAN"),
    ("DATE", "DATE"),
    ("TIME", "TIME"),
    ("DATETIME", "DATETIME"),
)

class SettingsModel(models.Model):
    field_name = models.CharField(max_length=255,null=False, blank=False)
    value = models.CharField(max_length=300)
    description = models.CharField(max_length=255,null=True)
    data_type = models.TextField(choices=DATA_TYPE,null=False, blank=False)
    is_active = models.BooleanField(default=False)


from django.db import models

from core_app.models import AbstractDate

# Create your models here.

sample_permission_config = {
    "status_update": ['*'], # '*', "clerk", "shop", "cut", "fit", "delivery", "received", "erect"
    "photo_upload": ['*'], # '*', "completed", "delivered", "issues"
}

class PermissionApp(models.Model, AbstractDate):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    
    permission_config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    

    def __str__(self):
        return self.name
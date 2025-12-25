from django.db import models
import uuid

from core_app.models import AbstractDate


from enum import IntEnum

class NotificationType(IntEnum):
    TOKEN = 1
    TOPIC = 2

NOTIFICATION_TYPE_CHOICES = [(tag.value, tag.name.capitalize()) for tag in NotificationType]

# Create your models here.
# NOTIFICATION_TYPE_CHOICES = [
#     (1, 'Token'), # Single user based
#     (2, 'Topic'), # Group Notification
# ]
class NotificationModel(AbstractDate, models.Model):


    notification_id = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    meta_data = models.JSONField(blank=True, null=True)  # Stores information like "from, to, platform, etc."
    notification_type = models.IntegerField(
        choices=NOTIFICATION_TYPE_CHOICES,
        default=1
    )
    is_active = models.BooleanField(default=True)
    request_data = models.JSONField(blank=True, null=True)  # Stores request data if needed
    response_data = models.JSONField(blank=True, null=True)  # Stores response data if needed
    

    def __str__(self):
        return f"{self.id}: Title:{self.title}"


class NotificationUserModel(models.Model):
    user = models.ForeignKey("user_app.UserDetail", on_delete=models.CASCADE)
    notification = models.ForeignKey(NotificationModel, on_delete=models.CASCADE, related_name='notification_users')
    is_seen = models.BooleanField(default=False)   # e.g., shown in dropdown
    is_read = models.BooleanField(default=False)   # e.g., clicked/viewed in detail
    delivered_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user} - {self.notification.title}"
    
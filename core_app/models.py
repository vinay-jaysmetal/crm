from django.utils import timezone
from django.db import models

# Create your models here.
class AbstractDate(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        

class AbstractUserSnapshotMixin(models.Model):
    # user = models.ForeignKey('user_app.UserDetail', on_delete=models.SET_NULL, null=True, blank=True)
    user_first_name = models.CharField(max_length=100)
    user_id_value = models.CharField(max_length=100)  # Avoid naming conflict with Django's internal `id`
    user_mobile = models.CharField(max_length=15)
    user_email = models.EmailField(max_length=100)

    class Meta:
        abstract = True
    
    # def set_user_snapshot(self, user):
    #     """Call this method to populate snapshot fields from a user instance."""
    #     # self.user = user
    #     self.user_first_name = user.first_name
    #     self.user_id_value = str(user.id)
    #     self.user_mobile = user.mobile
    #     self.user_email = user.email
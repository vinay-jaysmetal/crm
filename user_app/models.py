from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

from core_app.models import AbstractDate

# Create your models here.
AbstractUser._meta.get_field('email')._unique = True

class UserDetail(AbstractUser, AbstractDate):
    country_code = models.CharField(max_length=4)
    mobile = models.CharField(max_length=10, unique=True)
    
    profile_pic = models.FileField(null=False, blank=True, upload_to='profile_pics/%Y/%m/')
    
    is_temp_password = models.BooleanField(default=False)
    is_dev = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=True)
    
    notification_token = models.CharField(max_length=255, blank=True, null=True)
    
    # user_organizations = models.ManyToManyField(
    #     'organization_app.OrganizationModel',
    #     related_name='user_organizations',
    #     blank=True
    # )
    
    organization = models.ForeignKey(
        'organization_app.OrganizationModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    
    department = models.ForeignKey(
        'department_app.DepartmentModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    
    user_departments = models.ManyToManyField(
        'department_app.DepartmentModel',
        related_name='user_departments',
        blank=True,
        # null=True
    )
    
    security_key = models.CharField(max_length=6, blank=True, null=True, db_index=True) # for temporary user identifier when status updates from other user accounts
    
    role = models.ForeignKey(
        'user_app.Roles',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_roles_reference'
    )
    
    def __str__(self):        
        return str(self.id)
    
    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super(UserDetail, self).save(*args, **kwargs)
        
class Roles(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    permissions = models.JSONField() 
    access_details = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.name
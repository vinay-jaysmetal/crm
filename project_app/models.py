from django.db import models
from enum import IntEnum

from core_app.constants import DEPARTMENT_CHOICES
from core_app.models import AbstractDate, AbstractUserSnapshotMixin

PROJECT_STATUS_UPCOMING = "Upcoming"
PROJECT_STATUS_PENDING = "Pending"
PROJECT_STATUS_IN_PROGRESS = "In progress"
PROJECT_STATUS_CANCELLED = "Cancelled"
PROJECT_STATUS_ON_HOLD = "On Hold"
PROJECT_STATUS_COMPLETED = "Completed"

# Create your models here.
class ProjectStatus(models.IntegerChoices):
    UPCOMING = 1, PROJECT_STATUS_UPCOMING
    PENDING = 2, PROJECT_STATUS_PENDING
    IN_PROGRESS = 3, PROJECT_STATUS_IN_PROGRESS
    CANCELLED = 4, PROJECT_STATUS_CANCELLED
    ON_HOLD = 5, PROJECT_STATUS_ON_HOLD
    COMPLETED = 6, PROJECT_STATUS_COMPLETED
 

PROJECT_STATUSES = [
    {'id': 1, "name":PROJECT_STATUS_UPCOMING},
    {'id': 2, "name":PROJECT_STATUS_PENDING},
    {'id': 3, "name":PROJECT_STATUS_IN_PROGRESS},
    {'id': 4, "name":PROJECT_STATUS_CANCELLED},
    {'id': 5, "name":PROJECT_STATUS_ON_HOLD},
    {'id': 6, "name":PROJECT_STATUS_COMPLETED},
]
  
 

class ProjectModel(AbstractDate, models.Model ):
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(null=True, blank=True)
    
    image = models.FileField(null=False, blank=True, upload_to='project_images/%Y/%m/')
    
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    
    location_name = models.CharField(max_length=255, blank=True, null=True)
    location_address = models.CharField(max_length=255, blank=True, null=True)
    map_location_link = models.URLField(max_length=255, blank=True, null=True)
    # Pending, in progress, cancelled, on hold, completed
    status = models.IntegerField(choices=ProjectStatus.choices, default=ProjectStatus.UPCOMING)
    organization = models.ForeignKey(
        'organization_app.OrganizationModel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    total_unused_kg = models.FloatField(default=0)
    total_kg = models.FloatField(default=0)
    total_project_progress = models.FloatField(default=0)
    
    
    total_clerk_progress_percentage = models.FloatField(default=0)
    total_shop_progress_percentage = models.FloatField(default=0)
    total_cut_progress_percentage = models.FloatField(default=0)
    total_fit_progress_percentage = models.FloatField(default=0)
    total_delivery_progress_percentage = models.FloatField(default=0)
    total_received_progress_percentage = models.FloatField(default=0)
    total_erect_progress_percentage = models.FloatField(default=0)
    total_weld_progress_percentage = models.FloatField(default=0)
    total_delivery_3p_progress_percentage = models.FloatField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return str(self.id) +": " +self.name
    
    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"



class ProjectContact(AbstractDate, models.Model):
    contact_name = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    contact_role = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(max_length=100, blank=True, null=True)
    project = models.ForeignKey(
        ProjectModel,
        related_name='project_contacts',
        on_delete=models.CASCADE,
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.project.id) +": " +self.contact_name
    
    class Meta:
        verbose_name = "Project Contact"
        verbose_name_plural = "Project Contacts"



class ProjectTask(AbstractDate, models.Model):
    TASK_TYPE_CHOICES = [
        (1, "Task"),
        (2, "Issue"),
    ]
    AREA_CHOICES = [
        (1, "Shop"),
        (2, "Site"),
    ]

    image = models.FileField(null=True, blank=True, upload_to='project_task_images/%Y/%m/')
    notes = models.TextField(null=True, blank=True)
    task_type = models.IntegerField(choices=TASK_TYPE_CHOICES, default=1)
    area = models.IntegerField(choices=AREA_CHOICES, default=1)
    employee_name = models.CharField(max_length=100, blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        'user_app.UserDetail',
        on_delete=models.CASCADE,
        related_name='project_task_user',
        null=True,
        blank=True
    )
    project = models.ForeignKey(
        ProjectModel,
        related_name='project_tasks',
        on_delete=models.CASCADE,
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.get_task_type_display())
    
    class Meta:
        verbose_name = "Project Task"
        verbose_name_plural = "Project Tasks"

# class ActivityModel(AbstractDate, models.Model):
#     name = models.CharField(max_length=100)
#     description = models.CharField(max_length=255)
    
#     project = models.ForeignKey(
#         ProjectModel,
#         related_name='activities',
#         on_delete=models.CASCADE,
#     )
    
#     organization = models.ForeignKey(
#         'organization_app.OrganizationApp',
#         on_delete=models.SET_NULL,
#     )
    
#     is_active = models.BooleanField(default=True)
    
#     def __str__(self):
#         return self.name

class ProjectUserModel(AbstractUserSnapshotMixin, models.Model):
    project = models.ForeignKey(
        ProjectModel,
        related_name='user_projects',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        'user_app.UserDetail',
        related_name='project_users',
        on_delete=models.SET_NULL, null=True, blank=True
    )
    
    organization = models.ForeignKey(
        'organization_app.OrganizationModel',
        on_delete=models.CASCADE,
        related_name='project_users',
    )
    # department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    department = models.ForeignKey(
        'department_app.DepartmentModel',
        on_delete=models.PROTECT,
        default=1,
        related_name='ProjectUsersDepartment',
    )
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user_first_name} - {self.project.name} ({self.department})"
    
    # def __save__(self, *args, **kwargs):
    #     self.set_user_snapshot(self.user) # Call the set_user_snapshot
    
    class Meta:
        verbose_name = "Project User"
        verbose_name_plural = "Project Users"
        
        constraints = [
            models.UniqueConstraint(fields=['project', 'user'], name='unique_project_user'),
        ]
        

class OrganiseType(IntEnum):
    COMPLETED = 1
    DELIVERED = 2
    ISSUES = 3

ORGANISE_TYPE_CHOICES = [(tag.value, tag.name.capitalize()) for tag in OrganiseType]

class ProjectGalleryModel(models.Model):
    from project_app.utils import project_gallery_upload_path
    
    project = models.ForeignKey(ProjectModel, on_delete=models.CASCADE, related_name='project_galleries',null=False, blank=False)
    image = models.FileField(upload_to=project_gallery_upload_path, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)
    organise_type = models.IntegerField(choices=ORGANISE_TYPE_CHOICES, default=OrganiseType.COMPLETED)

    def __str__(self):
        return f"Image for Project {self.project.name}"

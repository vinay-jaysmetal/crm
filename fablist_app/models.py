from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from core_app.constants import DEPARTMENT_CHOICES
from core_app.models import AbstractDate, AbstractUserSnapshotMixin
from department_app.utils import get_department_qs_common_method
from fablist_app.utils import trigger_notification_on_first_fablist, update_fabrication_progress
from project_app.models import ProjectModel
from project_app.utils import update_project_progress

# Create your models here.

class FabricationListModel(AbstractDate, models.Model):
    # Recently called as Production list
    
    name = models.CharField(max_length=100, db_index=True)
    description = models.CharField(max_length=255, blank=True )
    categories = models.JSONField(blank=True, null=True)
    
    profile = models.CharField(max_length=255, blank=True)
    qty = models.IntegerField()
    kg = models.FloatField()
    total_kg = models.FloatField(default=0)
    total_progress = models.FloatField(default=0)
    
    # Production Status
    clerk_status = models.BooleanField(default=False)
    shop_status = models.BooleanField(default=False)
    cut_status = models.BooleanField(default=False)
    fit_status = models.BooleanField(default=False)
    delivery_status = models.BooleanField(default=False)
    received_status = models.BooleanField(default=False)
    erect_status = models.BooleanField(default=False)
    weld_status = models.BooleanField(default=False)
    delivery_3p_status = models.BooleanField(default=False)
    
    # Production Completed At
    clerk_completed_at = models.DateTimeField(blank=True, null=True)
    shop_completed_at = models.DateTimeField(blank=True, null=True)
    cut_completed_at = models.DateTimeField(blank=True, null=True)
    fit_completed_at = models.DateTimeField(blank=True, null=True)
    delivery_completed_at = models.DateTimeField(blank=True, null=True)
    received_completed_at = models.DateTimeField(blank=True, null=True)
    erect_completed_at = models.DateTimeField(blank=True, null=True)
    weld_completed_at = models.DateTimeField(blank=True, null=True)
    delivery_3p_completed_at = models.DateTimeField(blank=True, null=True)
    
    # Production Completed By   
    clerk_completed_by = models.ForeignKey('user_app.UserDetail',on_delete=models.SET_NULL,null=True, blank=True, related_name='clerk_completed_by')
    shop_completed_by = models.ForeignKey('user_app.UserDetail',on_delete=models.SET_NULL,null=True, blank=True, related_name='shop_completed_by')
    cut_completed_by = models.ForeignKey('user_app.UserDetail',on_delete=models.SET_NULL,null=True, blank=True, related_name='cut_completed_by')
    fit_completed_by = models.ForeignKey('user_app.UserDetail',on_delete=models.SET_NULL,null=True, blank=True, related_name='fit_completed_by')
    delivery_completed_by = models.ForeignKey('user_app.UserDetail',on_delete=models.SET_NULL,null=True, blank=True, related_name='delivery_completed_by')
    received_completed_by = models.ForeignKey('user_app.UserDetail',on_delete=models.SET_NULL,null=True, blank=True, related_name='received_completed_by')
    erect_completed_by = models.ForeignKey('user_app.UserDetail',on_delete=models.SET_NULL,null=True, blank=True, related_name='erect_completed_by')
    weld_completed_by = models.ForeignKey('user_app.UserDetail',on_delete=models.SET_NULL,null=True, blank=True, related_name='weld_completed_by')
    delivery_3p_completed_by = models.ForeignKey('user_app.UserDetail',on_delete=models.SET_NULL,null=True, blank=True, related_name='delivery_3p_completed_by')
    
    
    # Production ETA
    clerk_completion_time = models.CharField(max_length=100, blank=True, null=True)
    shop_completion_time = models.CharField(max_length=100, blank=True, null=True)
    cut_completion_time = models.CharField(max_length=100, blank=True, null=True)
    fit_completion_time = models.CharField(max_length=100, blank=True, null=True)
    delivery_completion_time = models.CharField(max_length=100, blank=True, null=True)
    received_completion_time = models.CharField(max_length=100, blank=True, null=True)
    erect_completion_time = models.CharField(max_length=100, blank=True, null=True)
    weld_completion_time = models.CharField(max_length=100, blank=True, null=True)
    delivery_3p_completion_time = models.CharField(max_length=100, blank=True, null=True)
    
    # Production Progress Percentage
    clerk_progress_percentage = models.FloatField(default=0)
    shop_progress_percentage = models.FloatField(default=0)
    cut_progress_percentage = models.FloatField(default=0)
    fit_progress_percentage = models.FloatField(default=0)
    delivery_progress_percentage = models.FloatField(default=0)
    received_progress_percentage = models.FloatField(default=0)
    erect_progress_percentage = models.FloatField(default=0)
    weld_progress_percentage = models.FloatField(default=0)
    delivery_3p_progress_percentage = models.FloatField(default=0)
    

    project = models.ForeignKey(
        ProjectModel,
        related_name='fablist_project',
        on_delete=models.CASCADE,
    )
    
    organization = models.ForeignKey(
        'organization_app.OrganizationModel',
        on_delete=models.PROTECT,
        related_name='fablist_organization',
    )
    
    incomplete_departments = models.JSONField(default=dict,null=True,blank=True) 
    class Meta:
        verbose_name = "Fabrication List"
        verbose_name_plural = "Fabrication Lists"
        
    def save(self, *args, **kwargs):
        self.total_kg = self.qty * self.kg if self.qty and self.kg else 0
        
        departments = get_department_qs_common_method().filter(is_active=True).values_list("name", flat=True)

        total_progress = 0
        for dept in departments:
            if getattr(self, f"{dept}_status", False):
                total_progress += 1
        self.total_progress = round( (total_progress / len(departments)) * 100,1)
        
        
        for dept in departments:
            status_field = f"{dept}_status"
            completed_at_field = f"{dept}_completed_at"
            progress_percentage_field = f"{dept}_progress_percentage"
            if getattr(self, status_field, False):
                setattr(self, progress_percentage_field, 100)
                # setattr(self, completed_at_field, self.updated_at)
            else:
                setattr(self, progress_percentage_field, 0)
                setattr(self, completed_at_field, None)
                
        trigger_notification_on_first_fablist(self.project)
        
        super().save(*args, **kwargs)           

@receiver(post_save, sender=FabricationListModel)
def post_save_fabrication_list(sender, instance, **kwargs):
    print("post_save_fabrication_list")
    update_project_progress(instance.project)
    
class FabricationStatusModel(AbstractUserSnapshotMixin, AbstractDate, models.Model):
    # Going to deprecate on structural changes, as there are no same departments users to complete a single production item
    fabrication_item = models.ForeignKey(FabricationListModel, related_name='statuses', on_delete=models.CASCADE)
    user = models.ForeignKey(
        'user_app.UserDetail',
        on_delete=models.CASCADE,
        related_name='fabricationstatus_user',
        null=True,
        blank=True
    ) # TODO DB corruption
    department = models.ForeignKey(
        'department_app.DepartmentModel',
        on_delete=models.PROTECT,
        related_name='fabricationstatus_department',
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('fabrication_item', 'user', 'department')
        verbose_name = "Fabrication Status"
        verbose_name_plural = "Fabrication Status"

    def save(self, *args, **kwargs):
        
        if not self.is_completed:
            self.completed_at = None
            print(f"set date to None {self.completed_at}")
        
        print("Saving FabricationStatusModel ",self.user)
        self.user_first_name = (f"{self.user.first_name} {self.user.last_name}") if self.user else ""
        self.user_id_value = str(self.user.id) if self.user else ""
        self.user_mobile = (f"{self.user.country_code} {self.user.mobile}") if self.user else ""
        self.user_email = self.user.email if self.user else ""
        
        super().save(*args, **kwargs)
        
        # Determine the dynamic field names
        dept_name = self.department.name  # e.g. 'clerk', 'shop'
        status_field = f"{dept_name}_status"
        completed_at_field = f"{dept_name}_completed_at"
        

        # Check if any other status entries for the same department and fabrication_item are completed
        all_dept_statuses = FabricationStatusModel.objects.filter(
            fabrication_item=self.fabrication_item,
            department=self.department
        )

        any_completed = all_dept_statuses.filter(is_completed=True).exists()

        # Update FabricationListModel
        fabrication = self.fabrication_item
        setattr(fabrication, status_field, any_completed)
        if any_completed:
            setattr(fabrication, completed_at_field, self.completed_at)
            print(f"Marking fab {fabrication.id} on {completed_at_field} to True at {self.completed_at}")
        else:
            setattr(fabrication, completed_at_field, None)
            print(f"Marking fab {fabrication.id} on {completed_at_field} to False")

        fabrication.save()

# signal on post save FabricationStatusModel
@receiver(post_save, sender=FabricationStatusModel)
def post_save_fabrication_status(sender, instance, **kwargs):
    print("post_save_fabrication_status")
    
    
    
    # update_fabrication_progress(instance.fabrication_item)

# {
#     "Status": true,
#     "Message": "Successfully retrieved fabrication weight report.",
#     "Data": {
#         "interval": "weekly",
#         "interval_from": "2025-11-01",
#         "interval_to": "2025-11-30",
#         "selected_departments": "",
#         "user_filter": null,
#         "data": [
#             {
#                 "Nov WEEK_44": {
#                     "clerk_completed_kg": 0.0,
#                     "clerk_completed_qty": 0.0,
#                     "shop_completed_kg": 0.0,
#                     "shop_completed_qty": 0.0,
#                     ....

#                 }
#             },
#             {
#                 "Nov WEEK_45": {
#                     "clerk_completed_kg": 0.0,
#                     "clerk_completed_qty": 0.0,
#                     "shop_completed_kg": 0.0,
#                     "shop_completed_qty": 0.0,
#                     ....

#                 }
#             }
#         ]
#     }
# }
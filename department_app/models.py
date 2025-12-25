from django.db import models

from core_app.constants import (
    CLERK_DEPARTMENT, SHOP_DEPARTMENT, CUT_DEPARTMENT, 
    FIT_DEPARTMENT, DELIVERY_DEPARTMENT, RECEIVED_DEPARTMENT, 
    ERECT_DEPARTMENT, WELD_DEPARTMENT, DELIVERY_3P_DEPARTMENT
)

DEPARTMENT_CHOICES = (
    (CLERK_DEPARTMENT, CLERK_DEPARTMENT),
    (SHOP_DEPARTMENT, SHOP_DEPARTMENT),
    (CUT_DEPARTMENT, CUT_DEPARTMENT),
    (FIT_DEPARTMENT, FIT_DEPARTMENT),
    (DELIVERY_DEPARTMENT, DELIVERY_DEPARTMENT),
    (RECEIVED_DEPARTMENT, RECEIVED_DEPARTMENT),
    (ERECT_DEPARTMENT, ERECT_DEPARTMENT),
    (WELD_DEPARTMENT, WELD_DEPARTMENT),
    (DELIVERY_3P_DEPARTMENT, DELIVERY_3P_DEPARTMENT),
    
)

# Create your models here.
class DepartmentModel(models.Model):
    name = models.CharField(max_length=100,choices=DEPARTMENT_CHOICES, unique=True,null=False, blank=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ['name']
from rest_framework import serializers

from department_app.models import DepartmentModel
from department_app.utils import get_department_qs_common_method
from project_app.models import ProjectUserModel
from .models import FabricationListModel, FabricationStatusModel
from django_solvitize.utils.DynamicFieldsModel import DynamicFieldsModelSerializer
from django.db.models import Q,F, FloatField, ExpressionWrapper, Avg


class FabricationStatusSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = FabricationStatusModel
        fields = '__all__'

class FabricationStatusDropdownSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = FabricationStatusModel
        fields = ('id', 'user', 'department', 'is_completed', 'completed_at')
        
class FabricationListSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = FabricationListModel
        fields = '__all__'


class UpdateFabricationListWithUserStatusSerializer(DynamicFieldsModelSerializer):
    all_users_statuses = serializers.SerializerMethodField()
    # report_data = serializers.SerializerMethodField()

    class Meta:
        model = FabricationListModel
        fields = [field.name for field in model._meta.get_fields() if field.concrete] + [
            "all_users_statuses"
        ]
    def get_all_users_statuses(self, obj):
        try:
            status_qs = FabricationStatusModel.objects.filter(
                fabrication_item=obj
            )
            if status_qs:
                return FabricationStatusSerializer(status_qs, many=True).data
            return []
        except Exception as e:
            print("User Status Error:", e)
            return []

class FabricationListWithUserStatusSerializer(DynamicFieldsModelSerializer):
    users_statuses = serializers.SerializerMethodField()
    overall_progress = serializers.SerializerMethodField()
    overall_status_progress = serializers.SerializerMethodField()
    all_users_statuses = serializers.SerializerMethodField()
    # report_data = serializers.SerializerMethodField()

    class Meta:
        model = FabricationListModel
        fields = [field.name for field in model._meta.get_fields() if field.concrete] + [
            "users_statuses", 
            "overall_progress",
            "overall_status_progress",
            "all_users_statuses"
        ]

    def get_report_data(self, obj):
        try:
            total_kg = obj.qty * obj.kg

            # Fetch all project users in one go
            project_users_qs = ProjectUserModel.objects.filter(project=obj.project).values("department")
            # Count project users department-wise
            dept_user_count = {}
            for row in project_users_qs:
                dept = row["department"]
                dept_user_count[dept] = dept_user_count.get(dept, 0) + 1

            # Fetch completed statuses for this fabrication item
            fabrication_status_qs = FabricationStatusModel.objects.filter(
                fabrication_item=obj, is_completed=True
            ).values("department__name")  # You can also add 'department_id' if needed

            completed_dept_count = {}
            for row in fabrication_status_qs:
                dept_name = row["department__name"]
                completed_dept_count[dept_name] = completed_dept_count.get(dept_name, 0) + 1

            report_data = {
                "total_kg": total_kg
            }

            # Reverse lookup to convert department ID to name (cached)
            department_names = {
                dept.id: dept.name for dept in DepartmentModel.objects.filter(name=dept_user_count.keys())
            }

            # Calculate percentage completed per department
            for dept_id, user_count in dept_user_count.items():
                dept_name = department_names.get(dept_id, f"{dept_id}")
                completed = completed_dept_count.get(dept_name, 0)
                percentage = round((completed / user_count) * 100, 2)
                report_data[dept_name.lower()] = percentage  # lowercase key for frontend consistency

            return report_data

        except Exception as e:
            print("Report Data Error:", e)
            return {}

    def get_users_statuses(self, obj):
        try:
            request_user = self.context.get("request").user
            status_obj = FabricationStatusModel.objects.filter(
                fabrication_item=obj, user=request_user
            ).first()
            if status_obj:
                return FabricationStatusSerializer(status_obj).data
            return None
        except Exception as e:
            print("User Status Error:", e)
            return None

    def get_all_users_statuses(self, obj):
        try:
            # request_user = self.context.get("request").user
            status_qs = FabricationStatusModel.objects.filter(
                fabrication_item=obj
            )
            if status_qs:
                return FabricationStatusSerializer(status_qs, many=True).data
            return []
        except Exception as e:
            print("User Status Error:", e)
            return []

    # def get_overall_progress(self, obj):
    def get_overall_status_progress(self, obj):
        
        
        # If you eventually store these status fields in FabricationListModel
        department_list =get_department_qs_common_method().values_list("name", flat=True)
        
        status_fields = [
            f"{dept}_status" for dept in department_list
        ]
        
        completed = sum(1 for field in status_fields if getattr(obj, field, False))
        return round((completed / len(status_fields)) * 100, 2)
    
    # def get_overall_status_progress(self, obj):
    def get_overall_progress(self, obj):

        # find avg of all dept status progress
        total_project_users = ProjectUserModel.objects.filter(project=obj.project)
        if total_project_users.count() == 0:
            return 0
      
        fab_obj = FabricationListModel.objects.get(id=obj.id)
      
        avaialble_department_user_count = total_project_users.filter(
            Q(department__name="clerk") |
            Q(department__name="shop") |
            Q(department__name="cut") |
            Q(department__name="fit") |
            Q(department__name="delivery") |
            Q(department__name="received") |
            Q(department__name="erect")
        ).values_list("department__name", flat=True).distinct().count()

        
        total_progress = (
            fab_obj.clerk_progress_percentage +
            fab_obj.shop_progress_percentage +
            fab_obj.cut_progress_percentage +
            fab_obj.fit_progress_percentage +
            fab_obj.delivery_progress_percentage +
            fab_obj.received_progress_percentage +
            fab_obj.erect_progress_percentage
        )
        return round(total_progress /avaialble_department_user_count, 2) or 0


# class FabricationListWithUserStatusSerializer(DynamicFieldsModelSerializer):
#     users_statuses = serializers.SerializerMethodField()
#     overall_progress = serializers.SerializerMethodField()
#     report_data = serializers.SerializerMethodField()
    
    
#     class Meta:
#         model = FabricationListModel
#         fields = [field.name for field in model._meta.get_fields() if field.concrete] + ["users_statuses", "overall_progress","report_data"]
    
#     def get_report_data(self, obj):
#         try:
#             report_data = {}
#             request_user = self.context.get("request").user
#             print("request_user", request_user)
#             # Get all users in the project
#             project_users_qs = ProjectUserModel.objects.filter(project=obj.project)
            
#             total_kg = obj.qty * obj.kg
#             report_data["total_kg"] = total_kg
            
#             project_users_dict = {}
#             for project_user in project_users_qs:
#                 # save total count of users departments wise
#                 project_users_dict[project_user.department] = project_users_dict.get(project_user.department, 0) + 1
                
            
#             total_fabrication_user_dict = {}
#             fabrication_status_qs = FabricationStatusModel.objects.filter(fabrication_item=obj,  is_completed=True)
#             print("fabrication_status_qs", fabrication_status_qs)
#             for fabrication_status in fabrication_status_qs:
#                 # save total count of users departments wise
#                 total_fabrication_user_dict[fabrication_status.department.name] = total_fabrication_user_dict.get(fabrication_status.department.name, 0) + 1
#             print("total_fabrication_user_dict", total_fabrication_user_dict)
                
#             print("project_users_qs", project_users_qs )
            
#             for project_user in project_users_qs:
#                 # save total count of users departments wise
                
#                 report_data[project_user.department] = round((total_fabrication_user_dict.get(project_user.department, 0) / project_users_dict.get(project_user.department, 0) * 100),2)
            
#             return report_data
            
#         except Exception as e:
#             print(e)
#             return None
        
#     def get_users_statuses(self, obj):
#         try:
#             request_user = self.context.get("request").user
#             print("request_user", request_user)
#             obj = FabricationStatusModel.objects.get(fabrication_item=obj,user=request_user)
#             return FabricationStatusSerializer(obj).data
#         except Exception as e:
#             print(e)
#             return None
        
#     def get_overall_progress(self, obj):
#         total_status_items = [
#             "clerk_status",
#             "shop_status",
#             "cut_status",
#             "fab_status",
#             "delivery_status",
#             "received_status",
#             "erect_status",
#         ]
#         total_completed_items = 0
#         for status in total_status_items:
#             # if obj.status is false then do not count it
#             if getattr(obj, status, False):
#                 total_completed_items += 1
#         total_items = len(total_status_items)

#         percentage = round((total_completed_items / total_items) * 100,2)

#         return percentage

    
    

class FabricationListDropdownSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = FabricationListModel
        fields = ('id', 'name')

class FabricationListReportSerializer(DynamicFieldsModelSerializer):
    overall_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = FabricationListModel
        fields = ('id', 'name','qty', 'kg','overall_progress')
        # ('id', 'name', 'qty', 'kg', 'profile')
    def get_overall_progress(self, obj):
        departments = get_department_qs_common_method().filter(is_active=True).values_list("name", flat=True)
        total_completed_items = 0
        for dept in departments:
            # if obj.status is false then do not count it
            if getattr(obj, f"{dept}_status", False):
                total_completed_items += 1
        total_items = len(departments)

        percentage = round((total_completed_items / total_items) * 100,2)

        return percentage

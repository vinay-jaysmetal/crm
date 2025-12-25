from django.shortcuts import render
from django_solvitize.utils.GlobalFunctions import *
from django_solvitize.utils.GlobalImports import (
    TokenAuthentication,
    AllowAny
)

from department_app.models import DepartmentModel
from department_app.serializers import DepartmentDropdownSerializer, DepartmentSerializer
from department_app.utils import get_department_qs_common_method
from fablist_app.models import FabricationListModel
from notification_app.models import NotificationUserModel
from project_app.models import PROJECT_STATUSES, ProjectModel
from settings_app.models import SettingsModel
from settings_app.serializers import SettingsSerializer
from user_app.models import UserDetail
from user_app.serializers import UserAppSerializer
from django.db.models import Count, Avg,Sum, F, FloatField, Q

# Create your views here.
class SplashAPIView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:            
            user = self.request.user
            user_detail_serializer = UserAppSerializer(user,) #exclude=['password'])
            user_details = user_detail_serializer.data
            settings_obj = SettingsModel.objects.filter(is_active=True)
            settings_serializer = SettingsSerializer(settings_obj, many=True)
            settings_data = settings_serializer.data
            
            departments_obj = DepartmentModel.objects.filter(is_active=True)
            departments_serializer = DepartmentDropdownSerializer(departments_obj, many=True)
            departments_data = departments_serializer.data
            

            # check for any unread notifications for the user
            unread_notification_count = NotificationUserModel.objects.filter(user=user, is_read=False).count()
            # notifications_serializer = NotificationUserSerializer(notifications_obj, many=True)
            # notifications_data = notifications_serializer.data
            
            
            # modal_obj = Modal.objects.filter(is_active=True)
            # modal_serializer = ModalSerializer(modal_obj, many=True)
            # modal_data = modal_serializer.data

            user_details_dict = {
                "user": user_details,
                "unread_notification_count": unread_notification_count,
                "departments": departments_data,
                "settings": settings_data,
                "project_status": PROJECT_STATUSES,
            }
            return ResponseFunction(1, "User details fetched successfully.", user_details_dict) 
        except Exception as e:
            print("Exception occured in userdetails fetching api", str(e))
            return ResponseFunction(0, "User details fetching failed.", {})       


class AdminDashboard(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        print("dashboard get ")
        
        required = []
        validation_errors = ValidateRequest(required, self.request.GET)

        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]["error"], {})
        else:
            print("Received required Fields")
        
        try:
            organization = self.request.GET.get("organization", "")
            end_date_from = self.request.GET.get("end_date_from", "")
            end_date_to = self.request.GET.get("end_date_to", "")
            
            dashboard_data = {} 
            project_qs = ProjectModel.objects.filter(status__in=[2, 3, 6]) # PENDING, IN_PROGRESS, COMPLETED
            users_qs  = UserDetail.objects.filter(is_active=True, is_superuser=False,)
            department_qs = get_department_qs_common_method().filter(is_active=True)
            
            all_projects_count = project_qs.count()
            
            if end_date_from:
                project_qs = project_qs.filter(end_date__gte=end_date_from)
            if end_date_to:
                project_qs = project_qs.filter(end_date__lte=end_date_to)
                
            fab_qs = FabricationListModel.objects.filter(project__in=project_qs)
            
            
            
                
            
            dashboard_data["end_date_from"] = end_date_from
            dashboard_data["end_date_to"] = end_date_to
            
            dashboard_data['projects'] = {}
            dashboard_data['projects']["all_projects"] = all_projects_count
            dashboard_data['projects']["total_projects"] = project_qs.count()
            dashboard_data['projects']["summary"] = project_qs.values('status').annotate(total=Count('id'))
            
            dashboard_data['users'] = {}
            dashboard_data['users']["total_users"] = users_qs.count()
            dashboard_data['users']["summary"] = users_qs.values('department').annotate(total=Count('id'))
            dashboard_data["total_departments"] = department_qs.count()
            
            
            departments = department_qs.values_list("name", flat=True)
            
            fab_summary ={}
            dashboard_data["fab_list_count"] = fab_qs.count()
            
            print("departments",departments)
            for dept in departments:
                if dept == "delivery 3p":
                    #  delivery 3p fix
                    dept = "delivery_3p"
                    
                print("Calculating for ",dept)
                # total kg alloted
                alloted = fab_qs.aggregate(
                    total_kg_alloted=Sum(F('qty') * F('kg'), output_field=FloatField())
                )['total_kg_alloted'] or 0.0

                # total kg used (only completed ones)
                used = fab_qs.filter(**{f"{dept}_status": True}).aggregate(
                    total_kg_used=Sum(F('qty') * F('kg'), output_field=FloatField())
                )['total_kg_used'] or 0.0

                # average progress
                avg_progress = project_qs.aggregate(
                    avg_progress=Avg(f"total_{dept}_progress_percentage")
                )['avg_progress'] or 0.0

                fab_summary[dept] = {
                    "avg_progress": round(avg_progress, 2),
                    "total_kg_used": round(used, 2),
                    "total_kg_alloted": round(alloted, 2)
                }

            dashboard_data["fab_summary"] = fab_summary
            
            # dashboard_data["fab_summary"] = {}
            # aggregations = {
            #     f'avg_{dept}': Avg(f'total_{dept}_progress_percentage')
            #     for dept in departments
            # }
            # # Use ** to unpack the dict into the aggregate call
            # averages = project_qs.filter().aggregate(**aggregations)
            # dashboard_data["fab_summary"] = averages

                
            
            
            return ResponseFunction(1, "Dashboard data fetched successfully.", dashboard_data) 
        except Exception as e:
            print("Exception occured in userdetails fetching api", str(e))
            return ResponseFunction(0, "Dashboard data fetching failed.", {})
            
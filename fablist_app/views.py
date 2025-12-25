import csv
from django.shortcuts import render
from django_solvitize.utils.custompagination import CustomPagination
from core_app.constants import DELIVERY_3P_DEPARTMENT, NON_DB_FIELDS as non_db_fields
from core_app.utils import get_bool_value, validate_fablist_file
from department_app.models import DepartmentModel
from department_app.utils import get_department_qs_common_method
from fablist_app.utils import trigger_notification_on_first_fablist
from notification_app.utils import send_notification_to_users
from organization_app.models import OrganizationModel
from project_app.models import PROJECT_STATUS_COMPLETED, ProjectModel, ProjectStatus, ProjectUserModel
from user_app.models import UserDetail
from django.utils.dateparse import parse_date
from django.db.models.functions import TruncMonth, TruncYear, TruncWeek, TruncDay, Trunc, Extract

from user_app.utils import get_user_qs_project_based
from .models import FabricationListModel, FabricationStatusModel
from .serializers import (
    FabricationListDropdownSerializer,
    FabricationListReportSerializer,
    FabricationListSerializer,
    FabricationListWithUserStatusSerializer,
    FabricationStatusDropdownSerializer,
    FabricationStatusSerializer,
    UpdateFabricationListWithUserStatusSerializer,
)


from django_solvitize.utils.GlobalFunctions import *
from django_solvitize.utils.GlobalImports import *

from django.db.models import Sum, Count, Avg, Q, F, ExpressionWrapper, FloatField, Case, When, Value
from django.utils import timezone

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar

# from datetime import datetime

# Create your views here.


class FabricationListAPI(ListAPIView):
    serializer_class = FabricationListSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    model = FabricationListModel

    def post(self, request, format=None):
        print(self.model.__name__, "-Post ", self.request.data)
        required = [
            "name",
        ]
        validation_errors = ValidateRequest(required, self.request.data)

        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]["error"], {})
        else:
            print("Received required Fields")

        try:
            id = self.request.POST.get("id", "")

            if id:
                qs = self.model.objects.get(id=id)
                msg = "Data updated"
                print(f"{self.model.__name__}: {msg} for id {id}")

                serializer = self.serializer_class(
                    qs, data=request.data, partial=True, context={"request": request}
                )

            else:
                serializer = self.serializer_class(
                    data=request.data, partial=True, context={"request": request}
                )
                msg = "Data saved"
                print(f"{self.model.__name__}: {msg} for new object")

            # from django.db import connection
            # print(f"Total queries: {len(connection.queries)}")
            # for q in connection.queries:
            #     print(q)

            serializer.is_valid(raise_exception=True)
            obj = serializer.save()

            print("obj.project ", obj.project)

            data = UpdateFabricationListWithUserStatusSerializer(obj).data

            return ResponseFunction(1, msg, data)

        except ValidationError as e:
            # Return validation error messages if data is invalid
            print("Validation error: ", e)
            return ResponseFunction(0, str(e), self.request.data)
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")

            return ResponseFunction(0, str(e), self.request.data)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        print("Get {}".format(self.model.__name__))
        print(f"Request params: {self.request.GET}")

        pk = self.kwargs.get("pk")
        qs = self.model.objects.all()
        # qs.delete()
        o = self.request.GET.get("o", "-id")
        if pk:
          return qs.filter(id=pk)

        # serializer change -start
        is_dropdown = self.request.GET.get("is_dropdown", "0")
        is_user_app = self.request.GET.get("is_user_app", "0")
        is_report = self.request.GET.get("is_report", "0")
        pagination = self.request.GET.get("pagination", "1")
        search = self.request.GET.get("search", "")
        exclude_id_list = json.loads(self.request.GET.get("exclude_id_list", "[]"))

        # serializer change filters
        if pagination == "0":
            print("Pagination None")
            self.pagination_class = None
            # qs = qs[:1000] # avoid loading entire DB table

        if is_user_app == "1":
            self.serializer_class = FabricationListWithUserStatusSerializer
        if is_dropdown == "1":
            self.serializer_class = FabricationListDropdownSerializer
            qs = qs.only("id", "name")
        if is_report == "1":
            self.serializer_class = FabricationListReportSerializer

        # serializer change -end

        filters = {}
        category_query = Q()  # initialize empty

        # Additional fields to filter - start
        all_keys = list(self.request.GET.keys())
        direct_fields = list(set(all_keys) - set(non_db_fields))
                
        db_fields = [f.name for f in self.model._meta.get_fields() if f.concrete]
        order_field = o.lstrip('-')  # handle '-' prefix for descending
        if o and order_field not in db_fields:
            return qs.none()


        # Filtering for direct fields
        for field in direct_fields:
            field_value = self.request.GET.get(field)
            print(f"Field: {field}, Value: {field_value}")
            if field_value is not None and field_value != "":
                # Special handling for fields if needed
                if field == "name" and field_value:
                    filters["name__contains"] = field_value
                elif field in ["is_active"]:
                    filters["is_active"] = get_bool_value(field_value)
                elif field == "categories":
                    field_value = json.loads(field_value or "[]")
                    if field_value:
                        print("field_value", field_value)
                        for cat in field_value:
                            category_query &= Q(categories__contains=[cat])
                else:
                    filters[field] = field_value
        # Additional fields to filter - end
        if search:
            qs = qs.filter(Q(name__icontains=search) 
                           |Q( profile__icontains=search)
                           )

        # Apply the category_query Q object if it has any conditions
        if category_query:
            print("*************** category_query", category_query)
            qs = qs.filter(category_query)
        
        if exclude_id_list:
            qs = qs.filter(**filters)
            qs = qs.exclude(id__in=exclude_id_list)
        else:
            qs = qs.filter(**filters)

        # Add filter logic for non db fields - start

        return qs.order_by(o)

    def delete(self, request):
        try:
            id = self.request.GET.get("id", "[]")
            if self.request.user.is_superuser:
                if id == "all":
                    self.model.objects.all().delete()
                    return ResponseFunction(1, "Deleted all data")
                else:
                    id = json.loads(id)
                    # print(id)
                    self.model.objects.filter(id__in=id).delete()
                    return ResponseFunction(1, "Deleted data having id " + str(id), {})
            else:
                if id == "all":
                    self.model.objects.all().delete()
                    return ResponseFunction(1, "Deleted all data")
                else:
                    id = json.loads(id)
                    # print(id)
                    self.model.objects.filter(id__in=id).delete()
                    return ResponseFunction(1, "Deleted data having id " + str(id), {})
                return ResponseFunction(0, "You are not allowed to delete data", {})

        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, "{} {}".format(self.model.__name__,str(e)) , {})

    def patch(self, request):
        try:
            print("Fablist patch Request data: {}".format(self.request.data))
            fablist = json.loads(self.request.data.get("fablist", "[]"))
            project = self.request.data.get("project", "")
            data = self.request.data

            fablist_file = request.FILES.get("fablist_file", None)

            # Validate file if present
            if fablist_file:
                is_valid, result = validate_fablist_file(fablist_file)

                if not is_valid:
                    return ResponseFunction(0, result, {})
                print(f"File validation result: {result}")
                fablist.extend(result)

            project_model_obj = ProjectModel.objects.get(id=project)
            res_status, res_message, res_reason = create_bulk_fabrication_list(
                project_model_obj, fab_list=fablist
            )

            if not res_status:
                return ResponseFunction(0, res_message, res_reason)

            return ResponseFunction(1, "Bulk fabrication list created", data)

        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, str(e), self.request.data)


def create_bulk_fabrication_list(model_obj, fab_list: list):
    """
    Create a bulk fabrication list from the request data.

    """
    is_success = False
    try:
        data = fab_list

        # Use bulk_create for efficiency
        fabrication_objects = []
        for item in data:
            cleaned_item = {
                "name": item.get("name", ""),
                "description": item.get("description", ""),
                "profile": item.get("profile", ""),
                "qty": item.get("qty", 0),
                "kg": item.get("kg", 0.0),
                "categories": item.get("categories", []),
                "clerk_completion_time": item.get("clerk_completion_time", ""),
                "shop_completion_time": item.get("shop_completion_time", ""),
                "cut_completion_time": item.get("cut_completion_time", ""),
                "fit_completion_time": item.get("fit_completion_time", ""),
                "delivery_completion_time": item.get("delivery_completion_time", ""),
                "received_completion_time": item.get("received_completion_time", ""),
                "erect_completion_time": item.get("erect_completion_time", ""),
                "weld_completion_time": item.get("weld_completion_time", ""),
                "delivery_3p_completion_time": item.get("delivery_3p_completion_time", ""),
                
            }
            fabrication_objects.append(
                FabricationListModel(
                    **cleaned_item,
                    project=model_obj,
                    organization=model_obj.organization if model_obj.organization else OrganizationModel.objects.all().first(),
                )
            )
        
        trigger_notification_on_first_fablist(model_obj)
        
        FabricationListModel.objects.bulk_create(fabrication_objects)
        is_success = True
        return is_success, "Data created", "Bulk fabrication list created successfully"
    except Exception as e:
        msg = f"Error creating bulk fabrication list: {e}"
        print(msg)
        return False, "Data not created", msg
    
    
        

class xFabricationStatusAPI(ListAPIView):
    serializer_class = FabricationStatusSerializer
    # authentication_classes = (TokenAuthentication,)
    # permission_classes = (IsAuthenticated,)

    model = FabricationStatusModel

    def post(self, request, format=None):
        print(self.model.__name__, " Post ", self.request.data)
        required = [
            "fabrication_item",
            "user",
            "department",
            "is_completed",
        ]
        is_completed = self.request.POST.get("is_completed", False)
        if get_bool_value(is_completed):
            required += ["completed_at"]
        validation_errors = ValidateRequest(required, self.request.data)

        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]["error"], {})
        else:
            print("Received required Fields")

        try:
            id = self.request.POST.get("id", "")
            fabrication_item = self.request.POST.get("fabrication_item", "")

            if id:
                fab_status_obj = self.model.objects.get(id=id)

                print("dept ", fab_status_obj.department.name)
                department_status = getattr(
                    fab_status_obj.fabrication_item,
                    f"{fab_status_obj.department.name}_status",
                    None,
                )
                print("dept status ", department_status)

                if department_status and get_bool_value(
                    self.request.POST.get("is_completed", False)
                ):
                    # Avoid duplicate completion of an item
                    return ResponseFunction(0, "This item is already completed", {})

                msg = "Data updated"
                print(f"{self.model.__name__}: {msg} for id {id}")

                serializer = self.serializer_class(
                    fab_status_obj,
                    data=request.data,
                    partial=True,
                    context={"request": request},
                )

            else:
                # TODO: Check this
                fab_status_qs = FabricationStatusModel.objects.filter(
                    fabrication_item=fabrication_item,
                    is_completed=True,
                    department=self.request.POST.get("department", ""),
                ).exists()

                if fab_status_qs:
                    return ResponseFunction(0, "This item is already completed", {})

                serializer = self.serializer_class(
                    data=request.data, partial=True, context={"request": request}
                )
                msg = "Data saved"
                print(f"{self.model.__name__}: {msg} for new object")

            # from django.db import connection
            # print(f"Total queries: {len(connection.queries)}")
            # for q in connection.queries:
            #     print(q)

            serializer.is_valid(raise_exception=True)
            obj = serializer.save()

            # data = self.serializer_class(obj).data
            # Return updated fab list to manage it on app side
            data = UpdateFabricationListWithUserStatusSerializer(obj.fabrication_item).data
            
            project_name = obj.fabrication_item.project.name
            full_name = obj.user.first_name + " " + obj.user.last_name
            fabitem_name = obj.fabrication_item.name
            
            users_qs = get_user_qs_project_based(obj.fabrication_item.project).exclude(id=obj.user.id)
            
            if get_bool_value(is_completed):
                print(users_qs, f"\nFabitem Update on {project_name}", f"\n{full_name} has completed fabitem ({fabitem_name}) on project ({project_name})")
                send_notification_to_users(users_qs, f"Fabitem Update on {project_name}", f"{full_name} has completed fabitem ({fabitem_name}) on project ({project_name})")
            else:
                print(users_qs, f"\nFabitem Update on {project_name}", f"\n{full_name} has reverted completion of fabitem ({fabitem_name}) on project ({project_name})")    
                send_notification_to_users(users_qs, f"Fabitem Update on {project_name}", f"{full_name} has reverted completion of fabitem ({fabitem_name}) on project ({project_name})")    

            return ResponseFunction(1, msg, data)

        except ValidationError as e:
            # Return validation error messages if data is invalid
            print("Validation error: ", e)
            return ResponseFunction(0, str(e), self.request.data)
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")

            return ResponseFunction(0, str(e), self.request.data)

    def get_queryset(self):
        print("Get {}".format(self.model.__name__))
        print(f"Request params: {self.request.GET}")

        qs = self.model.objects.all()

        # serializer change -start
        is_dropdown = self.request.GET.get("is_dropdown", "0")
        is_user_app = self.request.GET.get("is_user_app", "0")
        pagination = self.request.GET.get("pagination", "1")
        exclude_id_list = json.loads(self.request.GET.get("exclude_id_list", "[]"))

        # serializer change filters
        if pagination == "0":
            print("Pagination None")
            self.pagination_class = None
        if is_user_app == "1":
            self.serializer_class = self.serializer_class
        if is_dropdown == "1":
            self.serializer_class = FabricationStatusDropdownSerializer
            qs = qs.only("id", "name")
        # serializer change -end

        filters = {}

        # Additional fields to filter - start
        all_keys = list(self.request.GET.keys())
        direct_fields = list(set(all_keys) - set(non_db_fields))

        # Filtering for direct fields
        for field in direct_fields:
            field_value = self.request.GET.get(field)
            print(f"Field: {field}, Value: {field_value}")
            if field_value is not None and field_value != "":
                # Special handling for fields if needed
                if field == "name" and field_value:
                    filters["name__contains"] = field_value
                elif field in ["is_active"]:
                    filters["is_active"] = get_bool_value(field_value)
                else:
                    filters[field] = field_value
        # Additional fields to filter - end

        if exclude_id_list:
            qs = qs.filter(**filters)
            qs = qs.exclude(id__in=exclude_id_list)
        else:
            qs = qs.filter(**filters)

        # Add filter logic for non db fields - start

        return qs.order_by("-id")

    def delete(self, request):
        try:
            id = self.request.GET.get("id", "[]")
            if self.request.user.is_superuser:
                if id == "all":
                    self.model.objects.all().delete()
                    return ResponseFunction(1, "Deleted all data")
                else:
                    id = json.loads(id)
                    # print(id)
                    self.model.objects.filter(id__in=id).delete()
                    return ResponseFunction(1, "Deleted data having id " + str(id), {})
            else:
                if id == "all":
                    self.model.objects.all().delete()
                    return ResponseFunction(1, "Deleted all data")
                else:
                    id = json.loads(id)
                    # print(id)
                    self.model.objects.filter(id__in=id).delete()
                    return ResponseFunction(1, "Deleted data having id " + str(id), {})
                return ResponseFunction(0, "You are not allowed to delete data", {})

        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, "{} {}".format(self.model.__name__,str(e)) , {})


class FabReportListAPI(ListAPIView):
    model = FabricationListModel
    serializer_class = FabricationListSerializer

    def get(self, request, *args, **kwargs):
        try:
            required = ["project"]
            validation_errors = ValidateRequest(required, self.request.GET)

            if len(validation_errors) > 0:
                return ResponseFunction(0, validation_errors[0]["error"], {})
            else:
                print("Received required Fields")
            project = self.request.GET.get("project", "")

            # qs = self.model.objects.filter(project=self.request.GET.get("project"))

            # serializer = self.serializer_class(qs, many=True)
            # data = serializer.data

            departments = (
                get_department_qs_common_method()
                .filter(is_active=True)
                .values_list("name", flat=True)
            )

            queryset = self.model.objects.filter(project=project)

            # serializer = self.serializer_class(queryset, many=True)
            # data = serializer.data

            report = []

            total_kg = queryset.aggregate(total=Sum("kg"))["total"] or 0

            for dept in departments:
                print("dept ",dept)
                if dept == DELIVERY_3P_DEPARTMENT:
                    # Coorection fix for delivery_3p
                    dept = "delivery_3p"
                status_field = f"{dept}_status"
                completed_kg = (
                    queryset.filter(**{status_field: True}).aggregate(total=Sum("kg"))[
                        "total"
                    ]
                    or 0
                )
                total_count = queryset.count()
                completed_count = queryset.filter(**{status_field: True}).count()

                progress = (
                    (completed_count / total_count * 100) if total_count > 0 else 0
                )

                report.append(
                    {
                        "name": dept,
                        "progress": round(progress, 2),
                        "completed_sum_kg": round(completed_kg,2),
                        "total_sum_kg": round(total_kg,2),
                    }
                )

            return ResponseFunction(1, "Success", report)
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, str(e), self.request.data)


class FabUsersReportAPI(ListAPIView):
    model = FabricationListModel
    serializer_class = FabricationListSerializer

    def get(self, request, *args, **kwargs):
        try:
            required = []
            validation_errors = ValidateRequest(required, self.request.GET)
            if len(validation_errors) > 0:
                return ResponseFunction(0, validation_errors[0]["error"], {})
            else:
                print("Received required Fields")

            completed_from = self.request.GET.get("completed_from", "")
            completed_to = self.request.GET.get("completed_to", "")

            report_list = []

            user_qs = UserDetail.objects.filter(
                is_superuser=False,
                department__isnull=False,
                # organization=self.request.GET.get("organization", ""),
                # id=self.request.GET.get("user_id", "")
            )

            for user in user_qs:
                user_report = {
                    "user_data": {
                        "first_name": "",
                        "last_name": "",
                        "profile_pic": "",
                        "user_id": "",
                    },
                    "total_fab_items": 0,
                    "completed_fab_items": 0,
                    "total_projects": 0,
                    "completed_projects": 0,
                    "user_fablists": [],
                }
                # All fabrication statuses for this user
                fab_statuses = FabricationStatusModel.objects.filter(user=user)

                if completed_from:
                    fab_statuses = fab_statuses.filter(completed_at__gte=completed_from)
                if completed_to:
                    fab_statuses = fab_statuses.filter(completed_at__lte=completed_to)

                # .select_related(
                #     'fabrication_item__project', 'department'
                # )

                total_fab_items = fab_statuses.count()
                completed_fab_items = fab_statuses.filter(is_completed=True).count()

                # Get unique projects through the related fabrication_item
                total_projects = (
                    fab_statuses.values("fabrication_item__project_id")
                    .distinct()
                    .count()
                )
                completed_projects = (
                    fab_statuses.filter(
                        is_completed=True,
                        fabrication_item__project__status=ProjectStatus.COMPLETED,
                    )
                    .values("fabrication_item__project_id")
                    .distinct()
                    .count()
                )
                print(
                    "Project ",
                    fab_statuses.filter(
                        is_completed=True,
                        fabrication_item__project__status=ProjectStatus.COMPLETED,
                    ).values("fabrication_item__project_id"),
                )

                # Optional: List of fabrication items with status
                # user_fablists = list(
                #     fab_statuses.values(
                #         'fabrication_item__id',
                #         'fabrication_item__name',  # assuming this field exists
                #         'is_completed',
                #         'completed_at',
                #         'department__name',
                #         'fabrication_item__project__id',
                #         'fabrication_item__project__name',
                #         # 'fabrication_item__project_name'  # assuming this field exists
                #     )
                # )

                user_report = {
                    "user_data": {
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "phone": f"+{user.country_code}  {user.mobile}",
                        "profile_pic": (
                            user.profile_pic.url if user.profile_pic else ""
                        ),  # adjust as per your model
                        "user_id": user.id,
                        "department": user.department.id,
                    },
                    "total_fab_items": total_fab_items,
                    "completed_fab_items": completed_fab_items,
                    "overall_fab_completion_rate": (
                        round((completed_fab_items / total_fab_items) * 100, 2)
                        if total_fab_items
                        else 0
                    ),
                    "total_projects": total_projects,
                    "completed_projects": completed_projects,
                    "overall_project_completion_rate": (
                        round((completed_projects / total_projects) * 100, 2)
                        if total_projects
                        else 0
                    ),
                    # "user_fablists": user_fablists,
                }

                report_list.append(user_report)

            return ResponseFunction(1, "retrieve user report", report_list)

        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, str(e), self.request.data)

    def xget(self, request, *args, **kwargs):
        try:
            required = []
            validation_errors = ValidateRequest(required, self.request.GET)
            if len(validation_errors) > 0:
                return ResponseFunction(0, validation_errors[0]["error"], {})
            else:
                print("Received required Fields")

            completed_from = self.request.GET.get("completed_from", "")
            completed_to = self.request.GET.get("completed_to", "")

            report_list = []

            user_qs = UserDetail.objects.filter(
                is_superuser=False,
                department__isnull=False,
                # organization=self.request.GET.get("organization", ""),
                # id=self.request.GET.get("user_id", "")
            )

            for user in user_qs:
                user_report = {
                    "user_data": {
                        "first_name": "",
                        "last_name": "",
                        "profile_pic": "",
                        "user_id": "",
                    },
                    "total_fab_items": 0,
                    "completed_fab_items": 0,
                    "total_projects": 0,
                    "completed_projects": 0,
                    "user_fablists": [],
                }
                # All fabrication statuses for this user
                fab_statuses = FabricationStatusModel.objects.filter(user=user)

                if completed_from:
                    fab_statuses = fab_statuses.filter(completed_at__gte=completed_from)
                if completed_to:
                    fab_statuses = fab_statuses.filter(completed_at__lte=completed_to)

                # .select_related(
                #     'fabrication_item__project', 'department'
                # )

                total_fab_items = fab_statuses.count()
                completed_fab_items = fab_statuses.filter(is_completed=True).count()

                # Get unique projects through the related fabrication_item
                total_projects = (
                    fab_statuses.values("fabrication_item__project_id")
                    .distinct()
                    .count()
                )
                completed_projects = (
                    fab_statuses.filter(
                        is_completed=True,
                        fabrication_item__project__status=ProjectStatus.COMPLETED,
                    )
                    .values("fabrication_item__project_id")
                    .distinct()
                    .count()
                )
                print(
                    "Project ",
                    fab_statuses.filter(
                        is_completed=True,
                        fabrication_item__project__status=ProjectStatus.COMPLETED,
                    ).values("fabrication_item__project_id"),
                )

                # Optional: List of fabrication items with status
                # user_fablists = list(
                #     fab_statuses.values(
                #         'fabrication_item__id',
                #         'fabrication_item__name',  # assuming this field exists
                #         'is_completed',
                #         'completed_at',
                #         'department__name',
                #         'fabrication_item__project__id',
                #         'fabrication_item__project__name',
                #         # 'fabrication_item__project_name'  # assuming this field exists
                #     )
                # )

                user_report = {
                    "user_data": {
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "phone": f"+{user.country_code}  {user.mobile}",
                        "profile_pic": (
                            user.profile_pic.url if user.profile_pic else ""
                        ),  # adjust as per your model
                        "user_id": user.id,
                        "department": user.department.id,
                    },
                    "total_fab_items": total_fab_items,
                    "completed_fab_items": completed_fab_items,
                    "overall_fab_completion_rate": (
                        round((completed_fab_items / total_fab_items) * 100, 2)
                        if total_fab_items
                        else 0
                    ),
                    "total_projects": total_projects,
                    "completed_projects": completed_projects,
                    "overall_project_completion_rate": (
                        round((completed_projects / total_projects) * 100, 2)
                        if total_projects
                        else 0
                    ),
                    # "user_fablists": user_fablists,
                }

                report_list.append(user_report)

            return ResponseFunction(1, "retrieve user report", report_list)

        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, str(e), self.request.data)



class FabKgReportAPI(ListAPIView):
    serializer_class = FabricationListSerializer

    def get(self, request, *args, **kwargs):
        print("FabKgReportAPI Request: ", request.GET)
        try:
            required = ["interval"]
            interval = request.GET.get("interval")
            # organization = request.GET.get("organization")
            department = request.GET.get("department", "")
            user = request.GET.get("user")
            interval_from = request.GET.get("interval_from")
            interval_to = request.GET.get("interval_to")

            if interval not in ["daily", "weekly", "monthly", "yearly"]:
                return ResponseFunction(0, "Invalid interval. Choose from daily, weekly, monthly, yearly.", {})

            validation_errors = ValidateRequest(required, request.GET)
            if validation_errors:
                return ResponseFunction(0, validation_errors[0]["error"], {})

            status_qs = FabricationStatusModel.objects.filter(
                completed_at__isnull=False,
                # fabrication_item__organization_id=organization,
            )

            if interval_from:
                interval_from_dt = timezone.make_aware(datetime.strptime(interval_from, "%Y-%m-%d"))
                status_qs = status_qs.filter(completed_at__gte=interval_from_dt)
            if interval_to:
                interval_to_dt = timezone.make_aware(datetime.strptime(interval_to, "%Y-%m-%d"))
                status_qs = status_qs.filter(completed_at__lte=interval_to_dt)
            if user:
                status_qs = status_qs.filter(user=user)
            if department:
                status_qs = status_qs.filter(department=department)
            trunc_map = {
                "daily": TruncDay("completed_at"),
                "weekly": TruncWeek("completed_at"),
                "monthly": TruncMonth("completed_at"),
                "yearly": TruncYear("completed_at"),
            }
            trunc_func = trunc_map[interval]


            status_qs = status_qs.annotate(period=trunc_func).values("period").annotate(
                total_kg=Sum("fabrication_item__total_kg"),
                completed_kg=Sum("fabrication_item__total_kg", filter=Q(is_completed=True))
            ).order_by("period")
            
            # test = status_qs.annotate(
            #     item_total_kg=ExpressionWrapper(
            #         F("fabrication_item__qty") * F("fabrication_item__kg"),
            #         output_field=FloatField()
            #     ),
            #     fabrication_item__qty=F("fabrication_item__qty"),
            #     fabrication_item__total_kg=F("fabrication_item__kg")
                
            # ).first()
            
            # print("item_total_kg: ", test.item_total_kg)
            # print("fabrication_item__qty: ", test.fabrication_item__qty)
            # print("fabrication_item__total_kg: ", test.fabrication_item__total_kg)
            
            # status_qs = status_qs.annotate(
            #     item_total_kg=ExpressionWrapper(
            #         F("fabrication_item__qty") * F("fabrication_item__total_kg"),
            #         output_field=FloatField()
            #     )
            # ).annotate(
            #     period=trunc_func
            # ).values("period").annotate(
            #     total_kg=Sum("item_total_kg"),
            #     completed_kg=Sum("fabrication_item__kg", filter=Q(is_completed=True))
            # ).order_by("period")
            
            # print("status_qs: ", status_qs.query)
            

            formatted_list = []
            for entry in status_qs:
                period = entry["period"]
                if not period:
                    continue

                # Format based on interval
                if interval == "daily":
                    period_key = period.strftime("%Y-%m-%d")  # e.g., "2025-07-02"
                elif interval == "weekly":
                    period_key = period.strftime("%b WEEK_%U")
                elif interval == "monthly":
                    period_key = period.strftime("%b")
                elif interval == "yearly":
                    period_key = period.strftime("%Y")

                formatted_list.append({
                    period_key: {
                        "total_kg": round(entry["total_kg"] or 0, 2),
                        "completed_kg": round(entry["completed_kg"] or 0, 2),
                    }
                })

            report = {
                "interval": interval,
                "interval_from": interval_from,
                "interval_to": interval_to,
                # "organization": organization,
                "selected_departments": department,
                "user_filter": user,
                "data": formatted_list
            }

            return ResponseFunction(1, "Successfully retrieved fabrication weight report.", report)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return ResponseFunction(0, f"Error: {str(e)}", {})


class FabricationStatusAPI(ListAPIView):
    serializer_class = FabricationStatusSerializer
    model = FabricationStatusModel

    def post(self, request, format=None):
        print(self.model.__name__, " Post ", self.request.data)
        return handle_fabrication_status_update(request, request.data)


class FabricationStatusUpdateBulkAPI(ListAPIView):
    """
    API to bulk update fabrication statuses.
    Expected input:
    {
        "id_list": [1, 2, 3],
        "user": 5,
        "completed_at": "2025-11-14T10:00:00Z"
        "clerk": "1",
        "shop": "1",
        "cut": "1",
        "fit": "1",
        "weld": "1"
        "delivery": "1"
        "received": "1"
        "erect": "1"
        "delivery 3p": "1"
    }
    """
    model = FabricationListModel
    serializer_class = FabricationListSerializer
    

    def post(self, request, format=None):
        print(self.model.__name__, " Post ", self.request.data)
        
        required = [
            "id_list",
            "user",
        ]
        validation_errors = ValidateRequest(required, self.request.data)
        
        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]["error"], {})
        
        security_key = self.request.data.get("security_key", "")   
             
        if security_key:
            try:
                user_obj = UserDetail.objects.get(security_key=security_key)
            except UserDetail.DoesNotExist:
                return ResponseFunction(0, "Invalid security key", {})
            except UserDetail.MultipleObjectsReturned:
                return ResponseFunction(0, "Multiple users found with the same security key", {})
            except Exception as e:
                return ResponseFunction(0, f"Error retrieving user: {str(e)}", {})
        
        else:
            user_obj = UserDetail.objects.get(id=self.request.data.get("user"))
        
        id_list = json.loads(self.request.data.get("id_list", "[]"))
        
        completed_at = self.request.data.get("completed_at")
        
        available_departments = []
        
        clerk = self.request.data.get("clerk")
        shop = self.request.data.get("shop")
        cut = self.request.data.get("cut")
        fit = self.request.data.get("fit")
        weld = self.request.data.get("weld")
        delivery = self.request.data.get("delivery")
        received = self.request.data.get("received")
        erect = self.request.data.get("erect")
        delivery_3p = self.request.data.get("delivery 3p")
        
        if clerk:
            available_departments.append("clerk")
        if shop:
            available_departments.append("shop")
        if cut:
            available_departments.append("cut")
        if fit:
            available_departments.append("fit")
        if weld:
            available_departments.append("weld")
        if delivery:
            available_departments.append("delivery")
        if received:
            available_departments.append("received")
        if erect:
            available_departments.append("erect")
        if delivery_3p:
            available_departments.append("delivery 3p")
            
        
        
        if len(available_departments) == 0:
            return ResponseFunction(0, "At least one department should be selected", {})
        
        print("available_departments: ", available_departments)
        
        # Check wether the user has permission to update corresponding department before bulk operation
        user_departments = set(user_obj.user_departments.values_list("name", flat=True))
        requested_departments = set(available_departments)

        if not requested_departments.issubset(user_departments):
            return ResponseFunction(0, "User does not have permission for one or more departments", {})
                
        # TODO: bulk operation add/update need to perform on FabricationListModel
        for fab_item_id in id_list:
            fab_item_obj = self.model.objects.get(id=fab_item_id)
            
            if clerk:
                fab_item_obj.clerk_status = get_bool_value(clerk)
                fab_item_obj.clerk_completed_at = completed_at  or None
                fab_item_obj.clerk_completed_by = user_obj 
            
            if shop:
                fab_item_obj.shop_status = get_bool_value(shop)
                fab_item_obj.shop_completed_at = completed_at  or None
                fab_item_obj.shop_completed_by = user_obj
            
            if cut:
                fab_item_obj.cut_status = get_bool_value(cut)
                fab_item_obj.cut_completed_at = completed_at or None
                fab_item_obj.cut_completed_by = user_obj
            
            if fit:
                fab_item_obj.fit_status = get_bool_value(fit)
                fab_item_obj.fit_completed_at = completed_at or None
                fab_item_obj.fit_completed_by = user_obj
            
            if weld:
                fab_item_obj.weld_status = get_bool_value(weld)
                fab_item_obj.weld_completed_at = completed_at or None
                fab_item_obj.weld_completed_by = user_obj
                
            if delivery:
                fab_item_obj.delivery_status = get_bool_value(delivery)
                fab_item_obj.delivery_completed_at = completed_at or None
                fab_item_obj.delivery_completed_by = user_obj
                
            if received:
                fab_item_obj.received_status = get_bool_value(received)
                fab_item_obj.received_completed_at = completed_at or None
                fab_item_obj.received_completed_by = user_obj
                
            if erect:
                fab_item_obj.erect_status = get_bool_value(erect)
                fab_item_obj.erect_completed_at = completed_at or None
                fab_item_obj.erect_completed_by = user_obj
                
            if delivery_3p:
                fab_item_obj.delivery_3p_status = get_bool_value(delivery_3p)
                fab_item_obj.delivery_3p_completed_at = completed_at or None
                fab_item_obj.delivery_3p_completed_by = user_obj
            
            fab_item_obj.save()

        # project_fabs = self.model.objects.filter(project=fab_item_obj.project)
        
        # serializer = self.serializer_class(project_fabs, many=True)
        # data = serializer.data
        
        return ResponseFunction(1, "Data updated", {})
        

class FablistUploadViaFileView(APIView):
    model = FabricationListModel
    serializer_class = FabricationListSerializer
    def post(self, request, format=None):
        print(self.model.__name__, " Post ", self.request.data)
        fablist_file = request.FILES.get("fablist_file", None)
        project_id = request.data.get("project_id", None)
        
        project_obj = None
        
        if not project_id:
            return ResponseFunction(0, "Project id is required", {})
        
        if project_id:
            project_qs = ProjectModel.objects.filter(id=project_id)
            
            if project_qs.exists():
                project_obj = project_qs.first()
            else:
                return ResponseFunction(0, "Project not found", {})
        
                 # Validate file if present
        if fablist_file:
            is_valid, result = validate_fablist_file(fablist_file)
            
            if not is_valid:
                return ResponseFunction(0, result, {})

        if len(result) :#and not id:
            res_status, res_message, res_reason = create_bulk_fabrication_list(
                project_obj, result)
            print(f"Fabrication list status: {res_status}, {res_message}, {res_reason}")
            if res_status == 0:
                print(f"Error creating fabrication list: {res_message}, {res_reason}")
                msg = res_message + " " + res_reason
                raise ValidationError(msg)
            else:
                return ResponseFunction(1, "Fabrication list created", res_reason)
        else:
            return ResponseFunction(0, "Fabrication list is empty", {})


def handle_fabrication_status_update(request, data):
    """
    Shared function to handle creation/update logic for FabricationStatusModel
    Reused by both single and bulk update APIs.
    """
    model = FabricationStatusModel
    serializer_class = FabricationStatusSerializer

    required = [
        "fabrication_item",
        "user",
        "department",
        "is_completed",
    ]

    is_completed = data.get("is_completed", False)
    if get_bool_value(is_completed):
        required += ["completed_at"]

    validation_errors = ValidateRequest(required, data)
    if len(validation_errors) > 0:
        return ResponseFunction(0, validation_errors[0]["error"], {})

    try:
        id = data.get("id", "")
        fabrication_item = data.get("fabrication_item", "")

        if id:
            fab_status_obj = model.objects.get(id=id)

            department_status = getattr(
                fab_status_obj.fabrication_item,
                f"{fab_status_obj.department.name}_status",
                None,
            )

            if department_status and get_bool_value(data.get("is_completed", False)):
                return ResponseFunction(0, "This item is already completed", {})

            msg = "Data updated"
            serializer = serializer_class(
                fab_status_obj,
                data=data,
                partial=True,
                context={"request": request},
            )

        else:
            fab_status_qs = model.objects.filter(
                fabrication_item=fabrication_item,
                is_completed=True,
                department=data.get("department", ""),
            ).exists()

            if fab_status_qs:
                return ResponseFunction(0, "This item is already completed", {})

            serializer = serializer_class(
                data=data, partial=True, context={"request": request}
            )
            msg = "Data saved"

        serializer.is_valid(raise_exception=True)
        obj = serializer.save()

        # Return updated FabricationList data
        response_data = UpdateFabricationListWithUserStatusSerializer(obj.fabrication_item).data

        # Notifications
        project_name = obj.fabrication_item.project.name
        full_name = obj.user.first_name + " " + obj.user.last_name
        fabitem_name = obj.fabrication_item.name
        users_qs = get_user_qs_project_based(obj.fabrication_item.project).exclude(id=obj.user.id)

        if get_bool_value(is_completed):
            send_notification_to_users(
                users_qs,
                f"Fabitem Update on {project_name}",
                f"{full_name} has completed fabitem ({fabitem_name}) on project ({project_name})"
            )
        else:
            send_notification_to_users(
                users_qs,
                f"Fabitem Update on {project_name}",
                f"{full_name} has reverted completion of fabitem ({fabitem_name}) on project ({project_name})"
            )

        return ResponseFunction(1, msg, response_data)

    except Exception as e:
        print(f"Exception occurred {e} error at {printLineNo()}")
        return ResponseFunction(0, str(e), data)



def download_fabrication_data_csv(request, project_id):
    
    if not project_id:
        return HttpResponse("Project ID not provided")
    
    if not ProjectModel.objects.filter(id=project_id).exists():
        return HttpResponse("Project not found")
    
    # Filter fabrication data by project id
    fabrication_data = FabricationListModel.objects.filter(project_id=project_id)

    # Create the HttpResponse object with CSV headers.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Production_data_project_{project_id}.csv"'

    writer = csv.writer(response)
    
    # Write CSV header row (choose fields to include)
    headers = [
        'id', 'name', 'description', 'categories', 'profile', 'qty', 'kg', 'total_kg', 
        
        'clerk_status', 
        'clerk_completed_at',
        'clerk_completed_by',
        
        'shop_status', 
        'clerk_completed_at',
        'clerk_completed_by',
        
        
        'cut_status', 
        'clerk_completed_at',
        'clerk_completed_by',
        
        'fit_status', 
        'clerk_completed_at',
        'clerk_completed_by',
        
        'delivery_status', 
        'clerk_completed_at',
        'clerk_completed_by',
        
        'received_status',
        'clerk_completed_at',
        'clerk_completed_by',
        
        'erect_status', 
        'clerk_completed_at',
        'clerk_completed_by',
        
        'weld_status', 
        'clerk_completed_at',
        'clerk_completed_by',
        
        'delivery_3p_status'
        'clerk_completed_at',
        'clerk_completed_by',
        # add other fields as needed
    ]
    writer.writerow(headers)

    # Write data rows
    for fab in fabrication_data:
        row = [
            fab.id,
            fab.name,
            fab.description,
            ', '.join(fab.categories) if fab.categories else "",
            fab.profile,
            fab.qty,
            fab.kg,
            fab.total_kg,
            
            fab.clerk_status,
            fab.clerk_completed_at,
            fab.clerk_completed_by,
            
            fab.shop_status,
            fab.shop_completed_at,
            fab.shop_completed_by,
            
            fab.cut_status,
            fab.cut_completed_at,
            fab.cut_completed_by,
            
            
            fab.fit_status,
            fab.fit_completed_at,
            fab.fit_completed_by,
            
            fab.delivery_status,
            fab.delivery_completed_at,
            fab.delivery_completed_by,
            
            fab.received_status,
            fab.received_completed_at,
            fab.received_completed_by,
            
            fab.erect_status,
            fab.erect_completed_at,
            fab.erect_completed_by,
            
            fab.weld_status,
            fab.weld_completed_at,
            fab.weld_completed_by,
            
            fab.delivery_3p_status,
            fab.delivery_3p_completed_at,
            fab.delivery_3p_completed_by
        ]
        writer.writerow(row)

    return response


class NEWFabKgReportAPI(ListAPIView):
    serializer_class = FabricationListSerializer

    def get(self, request, *args, **kwargs):
        print("FabKgReportAPI Request: ", request.GET)
        try:
            required = ["interval"]
            interval = request.GET.get("interval")
            organization = request.GET.get("organization", "")
            department = request.GET.get("department", "")
            user = request.GET.get("user")
            interval_from = request.GET.get("interval_from")
            interval_to = request.GET.get("interval_to")

            if interval not in ["daily", "weekly", "monthly", "quarterly", "yearly"]:
                return ResponseFunction(0, "Invalid interval. Choose from daily, weekly, monthly, quarterly, yearly.", {})

            validation_errors = ValidateRequest(required, request.GET)
            if validation_errors:
                return ResponseFunction(0, validation_errors[0]["error"], {})

            # Filter FabricationListModel directly
            fab_qs = FabricationListModel.objects.all()

            # Apply organization filter
            if organization:
                fab_qs = fab_qs.filter(organization_id=organization)

            # Apply date range filter
            interval_from_dt = None
            interval_to_dt = None
            if interval_from:
                interval_from_dt = timezone.make_aware(datetime.strptime(interval_from, "%Y-%m-%d"))
                fab_qs = fab_qs.filter(created_at__gte=interval_from_dt)
            if interval_to:
                interval_to_dt = timezone.make_aware(datetime.strptime(interval_to, "%Y-%m-%d"))
                interval_to_dt = interval_to_dt.replace(hour=23, minute=59, second=59)
                fab_qs = fab_qs.filter(created_at__lte=interval_to_dt)

            # Apply other filters (adjust relations as needed)
            if user:
                fab_qs = fab_qs.filter(clerk_completed_by=user) | fab_qs.filter(shop_completed_by=user)  # etc.
            if department:
                # Adjust this based on your actual department relation
                pass

            trunc_map = {
                "daily": TruncDay("created_at"),
                "weekly": TruncWeek("created_at"),
                "monthly": TruncMonth("created_at"),
                "quarterly": TruncMonth("created_at"),
                "yearly": TruncYear("created_at"),
            }
            trunc_func = trunc_map[interval]

            # Query 1: Total KG
            total_qs = fab_qs.annotate(period=trunc_func).values('period').annotate(
                total_kg=Sum('total_kg')
            ).order_by('period')

            # Query 2: Completed KG
            completed_qs = fab_qs.filter(total_progress__gte=100).annotate(
                period=trunc_func
            ).values('period').annotate(
                completed_kg=Sum('total_kg')
            ).order_by('period')

            # ✅ FIXED: Single period_data dict - process both queries correctly
            period_data = {}
            
            # Process total_kg
            for entry in total_qs:
                if entry["period"]:
                    period_key = self._format_period_key(entry["period"], interval)
                    period_data[period_key] = {
                        "total_kg": round(entry["total_kg"] or 0, 2),
                        "completed_kg": 0.0
                    }

            # Process completed_kg
            for entry in completed_qs:
                if entry["period"]:
                    period_key = self._format_period_key(entry["period"], interval)
                    if period_key in period_data:
                        period_data[period_key]["completed_kg"] = round(entry["completed_kg"] or 0, 2)
                    else:
                        period_data[period_key] = {
                            "total_kg": 0.0,
                            "completed_kg": round(entry["completed_kg"] or 0, 2)
                        }

            # Generate COMPLETE continuous series
            continuous_data = self._generate_continuous_periods(
                interval, interval_from_dt, interval_to_dt, period_data
            )

            report = {
                "interval": interval,
                "interval_from": interval_from,
                "interval_to": interval_to,
                "selected_departments": department,
                "user_filter": user,
                "data": continuous_data
            }

            return ResponseFunction(1, "Successfully retrieved fabrication weight report.", report)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return ResponseFunction(0, f"Error: {str(e)}", {})

    def _format_period_key(self, period, interval):
        """✅ NEW: Format period to match your desired keys"""
        if interval == "daily":
            return period.strftime("%Y-%m-%d")
        # elif interval == "weekly":
        #     return period.strftime("%b WEEK_%U")
        elif interval == "weekly":
            return period.strftime("%b WEEK_%U")  # Sunday-based weeks matching 
        elif interval == "monthly":
            return period.strftime("%b %Y")
        elif interval == "quarterly":
            quarter = (period.month - 1) // 3 + 1
            return f"Q{quarter} {period.year}"
        else:  # yearly
            return period.strftime("%Y")

    def _generate_continuous_periods(self, interval, start_date, end_date, period_data):
        """Generate all periods in range with zeros for missing data"""
        continuous_list = []
        
        if not start_date or not end_date:
            return continuous_list

        current = start_date

        if interval == "weekly":
            # Align current to the Sunday of the week (TruncWeek uses Sunday start)
            days_to_sunday = (6 - current.weekday()) % 7
            current = current + timedelta(days=days_to_sunday)

        while current <= end_date:
            if interval == "daily":
                period_key = current.strftime("%Y-%m-%d")
                current += timedelta(days=1)

            elif interval == "weekly":
                period_key = current.strftime("%b WEEK_%U")  # Matches TruncWeek + %U

                # Append data or zero data
                data = period_data.get(period_key, {"total_kg": 0.0, "completed_kg": 0.0})
                continuous_list.append({period_key: data})

                current += timedelta(weeks=1)

            elif interval == "monthly":
                period_key = current.strftime("%b %Y")
                data = period_data.get(period_key, {"total_kg": 0.0, "completed_kg": 0.0})
                continuous_list.append({period_key: data})

                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

            elif interval == "quarterly":
                quarter = (current.month - 1) // 3 + 1
                period_key = f"Q{quarter} {current.year}"
                data = period_data.get(period_key, {"total_kg": 0.0, "completed_kg": 0.0})
                continuous_list.append({period_key: data})

                # Move to first month of next quarter
                if quarter == 4:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=quarter * 3 + 1)

            else:  # yearly
                period_key = current.strftime("%Y")
                data = period_data.get(period_key, {"total_kg": 0.0, "completed_kg": 0.0})
                continuous_list.append({period_key: data})

                current = current.replace(year=current.year + 1)

        return continuous_list


from django.shortcuts import render
from core_app.constants import NON_DB_FIELDS as non_db_fields
from core_app.utils import get_bool_value, validate_fablist_file
from fablist_app.views import create_bulk_fabrication_list
from notification_app.models import NotificationUserModel
from notification_app.utils import onesignal_push, send_notification_to_users
from project_app.utils import create_bulk_project_users
from user_app.models import UserDetail
from user_app.serializers import UserDetailDropdownSerializer

from .models import ProjectModel, ProjectUserModel, ProjectContact, ProjectTask
from .serializers import (ProjectDropdownSerializer, ProjectReportSerializer,
 ProjectSerializer, ProjectUserSerializer, ProjectWithUserSerializer, ProjectContactSerializer, 
 ProjectContactDropdownSerializer, ProjectTaskSerializer, ProjectTaskDropdownSerializer)

from django.contrib.auth import get_user_model
from django_solvitize.utils.GlobalFunctions import *
from django_solvitize.utils.GlobalImports import *
# Create your views here.
# from rest_framework.parsers import MultiPartParser, FormParser

class ProjectAPI(ListAPIView):
    serializer_class = ProjectSerializer
    # parser_classes = [MultiPartParser, FormParser]
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    model = ProjectModel
       
    def post(self, request, format=None):
        print(self.model.__name__," Post ",self.request.data)        
        required = ["name","organization","description"]
        validation_errors = ValidateRequest(required, self.request.data)
        
        # organization id will be pased
        organization = self.request.data.get("organization", None)
        
        fabrication_list = json.loads(self.request.data.get("fabrication_list", "[]"))
        
        # Expecting a list of user IDs for assingned_users_list
        assingned_users_list = json.loads(self.request.data.get("assingned_users_list", "[]")) 
        
        user_qs = UserDetail.objects.filter(id__in=assingned_users_list, organization=organization)
        print(f"Assigned Users QuerySet:{assingned_users_list} {user_qs}")
        
        if not user_qs.exists() and len(assingned_users_list) > 0:
            return ResponseFunction(0, f"No users found for this organization({organization})", {})
        
        # user_data = UserDetailDropdownSerializer(user_qs, many=True).data
        
        # return ResponseFunction(1, "Assingned users list updated", user_data)
        
        print(f"Fabrication List: {fabrication_list}")
        fablist_file = request.FILES.get("fablist_file", None)
        
         # Validate file if present
        if fablist_file:
            is_valid, result = validate_fablist_file(fablist_file)
            
            if not is_valid:
                return ResponseFunction(0, result, {})
            print(f"File validation result: {result}")
            fabrication_list.extend(result)
            
        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]['error'], {})
        else:
            print("Received required Fields")
            
        try:
            id = self.request.POST.get("id", "")
            
            with transaction.atomic():

                if id:
                    qs = self.model.objects.get(id=id)
                    msg = "Data updated"
                    print(f"{self.model.__name__}: {msg} for id {id}")
                    
                    serializer = self.serializer_class(
                        qs, data=request.data, partial=True,
                        context={'request': request}
                    )

                else:
                    serializer = self.serializer_class(data=request.data, partial=True,context={'request': request})
                    msg = "Data saved"
                    print(f"{self.model.__name__}: {msg} for new object")
                    
            
                # from django.db import connection
                # print(f"Total queries: {len(connection.queries)}")
                # for q in connection.queries:
                #     print(q)

                
                serializer.is_valid(raise_exception=True)
                project_obj = serializer.save()
                
                if len(fabrication_list) :#and not id:
                    res_status, res_message, res_reason = create_bulk_fabrication_list(project_obj, fabrication_list)
                    print(f"Fabrication list status: {res_status}, {res_message}, {res_reason}")
                    if res_status == 0:
                        print(f"Error creating fabrication list: {res_message}, {res_reason}")
                        msg = res_message + " " + res_reason
                        raise ValidationError(msg)
                    
                if len(assingned_users_list):# and not id:
                    # Bulk create users
                    res_status, res_message, res_reason = create_bulk_project_users(project_obj, user_qs)
                    if res_status == 0:
                        print(f"Error creating project users: {res_message}, {res_reason}")
                        msg = res_message + " " + res_reason
                        raise ValidationError(msg)
                    
                data = self.serializer_class(project_obj).data
            
            return ResponseFunction(1, msg,data)
        
        except ValidationError as e:
            # Return validation error messages if data is invalid
            print("Validation error: ",e)
            return ResponseFunction(0, str(e), self.request.data)
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")

            return ResponseFunction(0, str(e), self.request.data)
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        print("Get {}".format(self.model.__name__))
        print(f"Request params: {self.request.GET}")
        
        qs = self.model.objects.all()


        # serializer change -start
        is_dropdown = self.request.GET.get('is_dropdown', '0')
        is_user_app = self.request.GET.get('is_user_app', '0')
        is_report = self.request.GET.get('is_report', '0')
        pagination = self.request.GET.get('pagination', '1')
        search = self.request.GET.get('search', '')
        exclude_id_list = json.loads( self.request.GET.get('exclude_id_list', '[]'))
        start_date_from = self.request.GET.get('start_date_from', '')
        start_date_to = self.request.GET.get('start_date_to', '')
        end_date_from = self.request.GET.get('end_date_from', '')
        end_date_to = self.request.GET.get('end_date_to', '')
        
        
        
        # serializer change filters
        if pagination == '0':
            print("Pagination None")
            self.pagination_class = None
        if is_report == '1':
            self.serializer_class = ProjectReportSerializer
        if is_user_app == '1':
            self.serializer_class = ProjectWithUserSerializer
        if is_dropdown == '1':
            self.serializer_class = ProjectDropdownSerializer
            qs = qs.only('id', 'name')
        # serializer change -end       
        
        filters = {}
        
        additional_filter_fields = ['search','start_date_from', 'start_date_to', 'end_date_from', 'end_date_to']

        # Additional fields to filter - start
        all_keys = list(self.request.GET.keys())
        direct_fields = list(set(all_keys) - set(non_db_fields+additional_filter_fields))
        
        if search:
            qs = qs.filter(name__icontains=search)
            
        if start_date_from:
            qs = qs.filter(start_date__gte=start_date_from)
            
        if start_date_to:
            qs = qs.filter(start_date__lte=start_date_to)
            
        if end_date_from:
            qs = qs.filter(end_date__gte=end_date_from)
            
        if end_date_to:
            qs = qs.filter(end_date__lte=end_date_to)
        
        # Filtering for direct fields
        for field in direct_fields:
            field_value = self.request.GET.get(field)
            print(f"Field: {field}, Value: {field_value}")
            if field_value is not None and field_value != "":
                # Special handling for fields if needed
                if field == "name" and field_value:
                    filters["name__contains"] = field_value
                elif field == "organization" and field_value:
                    pass
                elif field == "search" and field_value:
                    filters["name__contains"] = field_value
                elif field in ["is_active"]:
                    filters["is_active"] =  get_bool_value(field_value )
                else:
                    filters[field] = field_value
        # Additional fields to filter - end    
        
        if exclude_id_list:
            qs = qs.filter(**filters)
            qs = qs.exclude(id__in=exclude_id_list  )
        else:
            qs = qs.filter(**filters)
            


        # Add filter logic for non db fields - start

        return qs.order_by('-id')


    def delete(self, request):
        try:
            id = self.request.GET.get('id', "[]")
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


class ProjectUserAPI(ListAPIView):
    serializer_class = ProjectUserSerializer
    # parser_classes = [MultiPartParser, FormParser]
    # authentication_classes = (TokenAuthentication,)
    # permission_classes = (IsAuthenticated,)

    model = ProjectUserModel
    
    def patch(self, request, format=None):
        # input add_user_ids, remove_user_ids
        try:
            required = ["project_id"]
            validation_errors = ValidateRequest(required, self.request.data)

            if len(validation_errors) > 0:  
                return ResponseFunction(0, validation_errors[0]['error'], {})
            else:
                print("Received required Fields")
                
            
            add_user_ids = json.loads(self.request.data.get("add_user_ids", "[]"))
            remove_user_ids = json.loads(self.request.data.get("remove_user_ids", "[]"))
            project_id = self.request.data.get("project_id", None)
            
            if len(add_user_ids) == 0 and len(remove_user_ids) == 0:
                return ResponseFunction(0, "No data to update", {})
            
            project_obj = ProjectModel.objects.filter(id=project_id).first()
            if not project_obj:
                return ResponseFunction(0, "No project found", {})
            
            add_user_qs = UserDetail.objects.filter(id__in=add_user_ids)
            remove_user_qs = UserDetail.objects.filter(id__in=remove_user_ids)
            
            with transaction.atomic():
                # Bulk create for add_user_ids
                print(f"add_user_qs: {add_user_qs}")
                res_status, res_message, res_reason = create_bulk_project_users(project_obj, add_user_qs)
                print(f"res_status: {res_status}, res_message: {res_message}, res_reason: {res_reason}")
                if res_status == 0:
                    print(f"Error creating project users: {res_message}, {res_reason}")
                    msg = res_message + " " + res_reason
                    raise ValidationError(msg)
                    
                # Bulk delete for remove_user_ids
                print(f"remove_user_qs: {remove_user_qs}")
                print(self.model.objects.filter(project=project_obj, user__in=remove_user_qs).delete())
                
            # notification_user_obj = NotificationUserModel.objects.create(user=to_user_obj,notification=obj)
            # print("notification_user_obj",notification_user_obj)    
  
            if len(add_user_qs) > 0:
                send_notification_to_users(add_user_qs, "Added to Project", f"You have been added to a project {project_obj.name}")
                
            if len(remove_user_qs) > 0:
                send_notification_to_users(remove_user_qs, "Removed from Project", f"You have been removed from a project {project_obj.name}")
                
                
            
                
            return ResponseFunction(1, "Project Users updated", {})
            
        except Exception as e:  
            print(f"Excepction occured {e} error at {printLineNo()}")
            msg = str(e)
            return ResponseFunction(0, msg, {})
       
    def post(self, request, format=None):
        return ResponseFunction(0, "Not allowed", {})
        print(self.model.__name__," Post ",self.request.data)        
        required = ["name","organization",]
        validation_errors = ValidateRequest(required, self.request.data)
        
        # organization id will be pased
        organization = self.request.data.get("organization", None)
        
        fabrication_list = json.loads(self.request.data.get("fabrication_list", "[]"))
        
        # Expecting a list of user IDs for assingned_users_list
        assingned_users_list = json.loads(self.request.data.get("assingned_users_list", "[]")) 
        
        user_qs = UserDetail.objects.filter(id__in=assingned_users_list, organization=organization)
        print(f"Assigned Users QuerySet:{assingned_users_list} {user_qs}")
        
        if not user_qs.exists() and len(assingned_users_list) > 0:
            return ResponseFunction(0, f"No users found for this organization({organization})", {})
        
        # user_data = UserDetailDropdownSerializer(user_qs, many=True).data
        
        # return ResponseFunction(1, "Assingned users list updated", user_data)
        
        print(f"Fabrication List: {fabrication_list}")
        fablist_file = request.FILES.get("fablist_file", None)
        
         # Validate file if present
        if fablist_file:
            is_valid, result = validate_fablist_file(fablist_file)
            
            if not is_valid:
                return ResponseFunction(0, result, {})
            print(f"File validation result: {result}")
            fabrication_list.extend(result)
            
        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]['error'], {})
        else:
            print("Received required Fields")
            
        try:
            id = self.request.POST.get("id", "")
            
            with transaction.atomic():

                if id:
                    qs = self.model.objects.get(id=id)
                    msg = "Data updated"
                    print(f"{self.model.__name__}: {msg} for id {id}")
                    
                    serializer = self.serializer_class(
                        qs, data=request.data, partial=True,
                        context={'request': request}
                    )

                else:
                    serializer = self.serializer_class(data=request.data, partial=True,context={'request': request})
                    msg = "Data saved"
                    print(f"{self.model.__name__}: {msg} for new object")
                    
            
                # from django.db import connection
                # print(f"Total queries: {len(connection.queries)}")
                # for q in connection.queries:
                #     print(q)

                
                serializer.is_valid(raise_exception=True)
                project_obj = serializer.save()
                
                if len(fabrication_list) :#and not id:
                    res_status, res_message, res_reason = create_bulk_fabrication_list(project_obj, fabrication_list)
                    print(f"Fabrication list status: {res_status}, {res_message}, {res_reason}")
                    if res_status == 0:
                        print(f"Error creating fabrication list: {res_message}, {res_reason}")
                        msg = res_message + " " + res_reason
                        raise ValidationError(msg)
                    
                if len(assingned_users_list):# and not id:
                    # Bulk create users
                    res_status, res_message, res_reason = create_bulk_project_users(project_obj, user_qs)
                    if res_status == 0:
                        print(f"Error creating project users: {res_message}, {res_reason}")
                        msg = res_message + " " + res_reason
                        raise ValidationError(msg)
                    
                data = self.serializer_class(project_obj).data
            
            return ResponseFunction(1, msg,data)
        
        except ValidationError as e:
            # Return validation error messages if data is invalid
            print("Validation error: ",e)
            return ResponseFunction(0, str(e), self.request.data)
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")

            return ResponseFunction(0, str(e), self.request.data)
  
    def get_queryset(self):
        print("Get {}".format(self.model.__name__))
        print(f"Request params: {self.request.GET}")
        
        qs = self.model.objects.all()


        # serializer change -start
        is_dropdown = self.request.GET.get('is_dropdown', '0')
        is_user_app = self.request.GET.get('is_user_app', '0')
        pagination = self.request.GET.get('pagination', '1')
        exclude_id_list = json.loads( self.request.GET.get('exclude_id_list', '[]'))
        
        # serializer change filters
        if pagination == '0':
            print("Pagination None")
            self.pagination_class = None
            # qs = qs[:1000] # avoid loading entire DB table
            qs = qs
        if is_user_app == '1':
            self.serializer_class = ProjectUserSerializer
        if is_dropdown == '1':
            self.serializer_class = ProjectUserSerializer
            qs = qs.only('id', 'name')
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
                    filters["is_active"] =  get_bool_value(field_value )
                else:
                    filters[field] = field_value
        # Additional fields to filter - end    
        
        if exclude_id_list:
            qs = qs.filter(**filters)
            qs = qs.exclude(id__in=exclude_id_list  )
        else:
            qs = qs.filter(**filters)
            


        # Add filter logic for non db fields - start

        return qs.order_by('-id')


    def delete(self, request):
        try:
            id = self.request.GET.get('id', "[]")
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



class ProjectContactAPI(ListAPIView):
    serializer_class = ProjectContactSerializer

    model = ProjectContact
       
    def post(self, request, format=None):
        print(self.model.__name__," Post ",self.request.data)        
        required = ["contact_name", 'project']
        validation_errors = ValidateRequest(required, self.request.data)

        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]['error'], {})
        else:
            print("Received required Fields")
            
        try:
            id = self.request.POST.get("id", "")

            if id:
                
                qs = self.model.objects.get(id=id)
                
                msg = "Data updated"
                print(f"{self.model.__name__}: {msg} for id {id}")
                
                serializer = self.serializer_class(
                    qs, data=request.data, partial=True,
                    context={'request': request}
                )

            else:
                serializer = self.serializer_class(data=request.data, partial=True,context={'request': request})
                msg = "Data saved"
                print(f"{self.model.__name__}: {msg} for new object")

            
            serializer.is_valid(raise_exception=True)
            obj = serializer.save()
            
            data = self.serializer_class(obj).data
            
            return ResponseFunction(1, msg,data)
        
        except ValidationError as e:
            # Return validation error messages if data is invalid
            print("Validation error: ",e)
            return ResponseFunction(0, str(e), self.request.data)
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")

            return ResponseFunction(0, str(e), self.request.data)
  
    def get_queryset(self):
        print("Get {}".format(self.model.__name__))
        print(f"Request params: {self.request.GET}")
        
        qs = self.model.objects.all()


        # serializer change -start
        is_dropdown = self.request.GET.get('is_dropdown', '0')
        is_user_app = self.request.GET.get('is_user_app', '0')
        pagination = self.request.GET.get('pagination', '1')
        exclude_id_list = json.loads( self.request.GET.get('exclude_id_list', '[]'))
        
        # serializer change filters
        if pagination == '0':
            print("Pagination None")
            self.pagination_class = None
            qs = qs # avoid loading entire DB table
        if is_user_app == '1':
            self.serializer_class = self.serializer_class
        if is_dropdown == '1':
            self.serializer_class = ProjectContactDropdownSerializer
            qs = qs.only('id', 'contact_name')
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
                if field == "contact_name" and field_value:
                    filters["contact_name__contains"] = field_value
                elif field in ["is_active"]:
                    filters["is_active"] =  get_bool_value(field_value )
                elif field in ["created_at", "updated_at"]:
                    filters[field + "__date"] = field_value
                else:
                    filters[field] = field_value
        # Additional fields to filter - end    
        
        if exclude_id_list:
            qs = qs.filter(**filters)
            qs = qs.exclude(id__in=exclude_id_list  )
        else:
            qs = qs.filter(**filters)
            


        # Add filter logic for non db fields - start

        return qs.order_by('-id')


    def delete(self, request):
        try:
            id = self.request.GET.get('id', "[]")
            if self.request.user.is_superuser:
                if id == "all":
                    self.model.objects.all().delete()
                    return ResponseFunction(1, "Deleted all data")
                else:
                    id = json.loads(id)
                    self.model.objects.filter(id__in=id).delete()
                    return ResponseFunction(1, "Deleted data having id " + str(id), {})
            else:
                if id == "all":
                    self.model.objects.all().delete()
                    return ResponseFunction(1, "Deleted all data")
                else:
                    id = json.loads(id)
                    self.model.objects.filter(id__in=id).delete()
                    return ResponseFunction(1, "Deleted data having id " + str(id), {})
                return ResponseFunction(0, "You are not allowed to delete data", {})
                
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, "{} {}".format(self.model.__name__,str(e)) , {})



class ProjectTaskAPI(ListAPIView):
    serializer_class = ProjectTaskSerializer
    model = ProjectTask
    
       
    def post(self, request, format=None):
        print(self.model.__name__," Post ",self.request.data)        
        required = ["task_type", 'project']
        validation_errors = ValidateRequest(required, self.request.data)

        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]['error'], {})
        else:
            print("Received required Fields")
            
        try:
            id = self.request.POST.get("id", "")

            if id:
                
                qs = self.model.objects.get(id=id)
                
                msg = "Data updated"
                print(f"{self.model.__name__}: {msg} for id {id}")
                
                serializer = self.serializer_class(
                    qs, data=request.data, partial=True,
                    context={'request': request}
                )

            else:
                serializer = self.serializer_class(data=request.data, partial=True,context={'request': request})
                msg = "Data saved"
                print(f"{self.model.__name__}: {msg} for new object")

            
            serializer.is_valid(raise_exception=True)
            obj = serializer.save()
            
            data = self.serializer_class(obj).data
            
            return ResponseFunction(1, msg,data)
        
        except ValidationError as e:
            # Return validation error messages if data is invalid
            print("Validation error: ",e)
            return ResponseFunction(0, str(e), self.request.data)
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")

            return ResponseFunction(0, str(e), self.request.data)
  
    def get_queryset(self):
        print("Get {}".format(self.model.__name__))
        print(f"Request params: {self.request.GET}")
        
        qs = self.model.objects.all()


        # serializer change -start
        is_dropdown = self.request.GET.get('is_dropdown', '0')
        is_user_app = self.request.GET.get('is_user_app', '0')
        pagination = self.request.GET.get('pagination', '1')
        exclude_id_list = json.loads( self.request.GET.get('exclude_id_list', '[]'))
        
        # serializer change filters
        if pagination == '0':
            print("Pagination None")
            self.pagination_class = None
            qs = qs # avoid loading entire DB table
        if is_user_app == '1':
            self.serializer_class = self.serializer_class
        if is_dropdown == '1':
            self.serializer_class = ProjectTaskDropdownSerializer
            qs = qs.only('id', 'task_type')
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
                if field in ["is_active"]:
                    filters["is_active"] =  get_bool_value(field_value )
                elif field in ["created_at", "updated_at"]:
                    filters[field + "__date"] = field_value
                else:
                    filters[field] = field_value
        # Additional fields to filter - end    
        
        if exclude_id_list:
            qs = qs.filter(**filters)
            qs = qs.exclude(id__in=exclude_id_list  )
        else:
            qs = qs.filter(**filters)
            


        # Add filter logic for non db fields - start

        return qs.order_by('-id')


    def delete(self, request):
        try:
            id = self.request.GET.get('id', "[]")
            if self.request.user.is_superuser:
                if id == "all":
                    self.model.objects.all().delete()
                    return ResponseFunction(1, "Deleted all data")
                else:
                    id = json.loads(id)
                    self.model.objects.filter(id__in=id).delete()
                    return ResponseFunction(1, "Deleted data having id " + str(id), {})
            else:
                if id == "all":
                    self.model.objects.all().delete()
                    return ResponseFunction(1, "Deleted all data")
                else:
                    id = json.loads(id)
                    self.model.objects.filter(id__in=id).delete()
                    return ResponseFunction(1, "Deleted data having id " + str(id), {})
                return ResponseFunction(0, "You are not allowed to delete data", {})
                
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, "{} {}".format(self.model.__name__,str(e)) , {})


class BulkUpdateProjectTaskAPI(ListAPIView):
    model = ProjectTask
    serializer_class = ProjectTaskSerializer
    
    def post(self, request, *args, **kwargs):
        from django.utils import timezone
        try:
            print(self.model.__name__," Post ",self.request.data)
            # Extract ID list and update fields
            id_list = json.loads(request.data.get("id_list", "[]"))
            employee_name = request.data.get("employee_name")
            is_completed = request.data.get("is_completed")
            completed_at = get_bool_value(request.data.get("completed_at"))
            
            required = ["id_list"]
            validation_errors = ValidateRequest(required, self.request.data)

            if len(validation_errors) > 0:
                return ResponseFunction(0, validation_errors[0]['error'], {})
            else:
                print("Received required Fields")

            # Fetch tasks
            tasks = self.model.objects.filter(id__in=id_list)

            if not tasks.exists():
                return ResponseFunction(0, "No tasks found for given IDs", {})

            # Prepare update dict
            update_fields = {}
            if employee_name is not None:
                update_fields["employee_name"] = employee_name
                
            if is_completed is not None:
                update_fields["is_completed"] = is_completed
                # auto-set completed_at when marking as completed
                if is_completed and not completed_at:
                    update_fields["completed_at"] = timezone.now()
                elif not is_completed:
                    update_fields["completed_at"] = None
                    
            if completed_at is not None:
                update_fields["completed_at"] = completed_at
                
            completed_by = self.request.user.id
            if completed_by is not None:
                update_fields["completed_by"] = completed_by

            if not update_fields:
                return ResponseFunction(0, "No fields to update", {})

            # Perform bulk update
            tasks.update(**update_fields)

            msg = f"{tasks.count()} tasks updated successfully"
            updated_data = self.serializer_class(tasks, many=True).data
            return ResponseFunction(1, msg, updated_data)

        except Exception as e:
            print(f"Exception occurred: {e} at {printLineNo()}")
            return ResponseFunction(0, str(e), request.data)
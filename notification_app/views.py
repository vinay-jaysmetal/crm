from django.shortcuts import render
from core_app.constants import NON_DB_FIELDS as non_db_fields
from core_app.utils import get_bool_value
from department_app.utils import get_department_qs_common_method
from notification_app.utils import onesignal_push
from user_app.models import UserDetail

from .models import NotificationModel, NotificationUserModel
from .serializers import NotificationDropdownSerializer, NotificationSerializer, NotificationUserSerializer

from django_solvitize.utils.GlobalFunctions import *
from django_solvitize.utils.GlobalImports import *
# Create your views here.


class NotificationAPI(ListAPIView):
    serializer_class = NotificationSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    model = NotificationModel
       
    def post(self, request, format=None):
        print(self.model.__name__," Post ",self.request.data)        
        required = ["title"]
        validation_errors = ValidateRequest(required, self.request.data)

        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]['error'], {})
        else:
            print("Received required Fields")
            
        try:
            id = self.request.POST.get("id", "")
            title = self.request.POST.get("title", "")
            description = self.request.POST.get("description", "")
            image_url = self.request.POST.get("image_url", "")
            # to_user_id = self.request.POST.get("to_user_id", "")
            
            to_user_obj = UserDetail.objects.get(id=self.request.user.id)

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
            
            # if to_user_id:
                # create NotificationUserModel
            notification_user_obj = NotificationUserModel.objects.create(user=to_user_obj,notification=obj)
            print("notification_user_obj",notification_user_obj)
            
            payload = {
                "title": title,
                "description": description,
                "image_url": image_url
            }
            
            # try:
            #     onesignal_push.delay(lst_tokens=[to_user_obj.notification_token], payload=payload, type="normal", data={"notification_id":obj.id})
            # except Exception as e:
            #     print(f"Celery Failed: Error sending notification: {e}")
            onesignal_response = onesignal_push(lst_tokens=[to_user_obj.notification_token], payload=payload, type="normal", data={"notification_id":obj.id})
            
            # pass context to serializer
            data = self.serializer_class(obj,context={'request': request}).data
            
            data['onesignal_response']= onesignal_response
            
            return ResponseFunction(1, msg,data)
        
        
        
        except UserDetail.DoesNotExist:
            return ResponseFunction(0, "Invalid to_user_id provided", {})
        
        except ValidationError as e:
            # Return validation error messages if data is invalid
            print("Validation error: ",e)
            msg = f"Error creating {self.model.__name__}: {e}, {printLineNo()}"
            return ResponseFunction(0, msg, self.request.data)
        except Exception as e:
            msg = f"Error creating {self.model.__name__}: {e}, {printLineNo()}"
            print(f"Excepction occured {e} error at {printLineNo()}")

            return ResponseFunction(0, msg, self.request.data)
  
    def get_queryset(self):
        print("Get {}".format(self.model.__name__))
        print(f"Request params: {self.request.GET}")
        
        qs = self.model.objects.all()
        
        qs =  NotificationModel.objects.filter(
            # notification_users__user=self.request.user
            Q(notification_users__user=self.request.user) | Q(notification_users__user__isnull=True)
        )#.distinct().order_by('-id')


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
            self.serializer_class = NotificationDropdownSerializer
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


class NotificationUserAPI(ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    model = NotificationUserModel
    serializer_class = NotificationUserSerializer
    
    def patch(self, request):
        try:
            required = ["notification_ids", "operation"]
            validation_errors = ValidateRequest(required, self.request.POST)

            if len(validation_errors) > 0:
                return ResponseFunction(0, validation_errors[0]["error"], {})
            else:
                print("Received required Fields")
            
            
            notification_ids = json.loads(self.request.data.get('notification_ids', '[]'))
            operation = self.request.data.get('operation', 'read')  
            
            qs = NotificationUserModel.objects.filter(notification__in=notification_ids).filter(user=self.request.user)
            if not qs.exists():
                return ResponseFunction(0, "Invalid notification_ids provided", {})
            
            match operation:
                case "mark_as_read":
                    qs.update(is_read=True, )
                    msg = "Notification marked as read"
                case "mark_as_unread":
                    qs.update(is_read=False, )
                    msg = "Notification marked as unread"
                case "mark_as_seen":
                    qs.update(is_seen=True, )
                    msg = "Notification marked as seen"
                case "mark_as_unseen":
                    qs.update(is_seen=False, )
                    msg = "Notification marked as unseen"
                case _:
                    return ResponseFunction(0, "Invalid operation provided - must be [mark_as_read, mark_as_unread, mark_as_seen, mark_as_unseen]", {})
            
            return ResponseFunction(1, msg, {"notification_ids": notification_ids, "operation": operation})
            
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, "{} {}".format(self.model.__name__,str(e)), {})
    
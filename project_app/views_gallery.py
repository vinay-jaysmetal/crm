from django.shortcuts import render
from core_app.constants import NON_DB_FIELDS as non_db_fields
from notification_app.utils import send_notification_to_users
from user_app.utils import get_user_qs_project_based

from .models import ORGANISE_TYPE_CHOICES, OrganiseType, ProjectGalleryModel
from .serializers import ProjectGallerySerializer

from django.contrib.auth import get_user_model
from django_solvitize.utils.GlobalFunctions import *
from django_solvitize.utils.GlobalImports import *
# Create your views here.

class ProjectGalleryAPI(ListAPIView):
    serializer_class = ProjectGallerySerializer
    # parser_classes = [MultiPartParser, FormParser]
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    model = ProjectGalleryModel
       
   
    def post(self, request, format=None):
        print(self.model.__name__," Post ",self.request.data)        
        required = ["project",]
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
            
            users_qs = get_user_qs_project_based(obj.project).exclude(id=self.request.user.id)
            print("users_qs ",users_qs)
            user_full_name = self.request.user.first_name + " " + self.request.user.last_name
            
            print("ORGANISE_TYPE_CHOICES ",ORGANISE_TYPE_CHOICES)
            title = f"{OrganiseType(obj.organise_type).name.capitalize()} picture uploaded on {obj.project.name}"
            
            article = "an" if obj.organise_type == 3 else "a"
            organise_type = OrganiseType(obj.organise_type).name.lower()
            caption = f"({obj.caption}) " if obj.caption else ""
            content = f"{user_full_name} has uploaded {article} {organise_type} {caption}picture on {obj.project.name}"
            
            print(users_qs, title , content)
            send_notification_to_users(users_qs, title , content)
            
            
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
            
        # if is_user_app == '1':
        #     self.serializer_class = ProjectUserSerializer
        # if is_dropdown == '1':
        #     self.serializer_class = ProjectUserSerializer
        #     qs = qs.only('id', 'name')
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



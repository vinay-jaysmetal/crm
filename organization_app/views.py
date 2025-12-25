from django.shortcuts import render
from core_app.constants import NON_DB_FIELDS as non_db_fields

from .models import OrganizationModel
from .serializers import OrganizationDropdownSerializer, OrganizationSerializer

from django_solvitize.utils.GlobalFunctions import *
from django_solvitize.utils.GlobalImports import *
# Create your views here.


class OrganizationAPI(ListAPIView):
    serializer_class = OrganizationSerializer
    # authentication_classes = (TokenAuthentication,)
    # permission_classes = (IsAuthenticated,)

    model = OrganizationModel
       
    def post(self, request, format=None):
        print(self.model.__name__," Post ",self.request.data)        
        required = ["name",]
        validation_errors = ValidateRequest(required, self.request.data)

        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]['error'], {})
        else:
            print("Received required Fields")
            
        try:
            id = self.request.POST.get("id", "")

            if id:
                # qs = self.model.objects.filter(id=id)
                # if not qs.exists():
                #     return ResponseFunction(0, "Detail Not Found", {})
                
                qs = self.model.objects.get(id=id)
                
                # qs = get_object_or_404(self.model,id=id)
                
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
            self.serializer_class = OrganizationDropdownSerializer
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



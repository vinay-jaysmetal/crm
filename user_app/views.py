from django.shortcuts import render
from core_app.redis_client import redis_client
from core_app.constants import CLERK_DEPARTMENT, NON_DB_FIELDS as non_db_fields, SHOP_DEPARTMENT, TEST_OTP
from core_app.exceptions import DefaultException
from core_app.utils import django_send_email, filter_valid_fields, generate_password, get_bool_value, validate_request, verify_otp
from django_solvitize.utils.GlobalFunctions import *
from django_solvitize.utils.GlobalImports import (
    TokenAuthentication,
    AllowAny
)
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken  
from department_app.models import DepartmentModel
from organization_app.models import OrganizationModel
from user_app.models import Roles, UserDetail
from user_app.serializers import RoleDropdownSerializer, RoleSerializer, UserAppSerializer, UserDetailDropdownSerializer, UserSerializer, UserSerializerSafe
from user_app.utils import check_security_key_is_unique


# Create your views here.
# Todos
# CRUD View - create user, edit user, view user, delete user
# login - basic auth (username and password)
# logout - logout user: clear session and cookies
# Forgot Password or Reset Password
# 
#


class UserAPI(ListAPIView):
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (IsAuthenticated,)
    current_user = None
    model = UserDetail
    
    
    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        # context['unblurr'] = self.request.GET.get('unblurr', 'False').lower() == 'true'
        # print("In context",self.current_user.unblur_list)
        # print("In context",self.current_user.seen_customers)
        

        # context['from_user_id'] = self.current_user.id
        return context
    
    def get_queryset(self):
        print("Get UserAPI")
        
        self.current_user = self.request.user

        # serializer change -start
        is_dropdown = self.request.GET.get('is_dropdown', '0')
        is_user_app = self.request.GET.get('is_user_app', '0')
        pagination = self.request.GET.get('pagination', '1')
        search = self.request.GET.get('search', '')
        exclude_id_list = json.loads( self.request.GET.get('exclude_id_list', '[]'))
        
        is_superuser = self.request.user.is_superuser
        if is_superuser:
            qs = self.model.objects.all()
        else:
            qs = self.model.objects.all().filter(is_superuser=False)  
        
        filters = {}
        exclude = {}
        # serializer change filters
        if is_user_app == '1':
            self.serializer_class = UserAppSerializer
            # exclude["id__in"] = self.current_user.seen_customers or []
            # filters['is_superuser'] = False
            # filters['is_active'] = True
            qs = qs.filter(~Q(id=self.current_user.id)) 
            print("QS count ", qs.count())
        
        if pagination == '0':
             self.pagination_class = None
            
        if is_dropdown == '1':
            self.serializer_class = UserDetailDropdownSerializer
        # serializer change -end
        
        
        # JSON Field filter - start
        # data_set_fields = list(OPTIONS_JSON.keys())
        
        
        
        # for category in data_set_fields:
        #     category_data = self.request.GET.get(category, None)
        #     if category_data:
        #         try:
        #             # Parse the JSON string to a dictionary
        #             category_dict = json.loads(category_data)
        #         except json.JSONDecodeError:
        #             raise ValidationError({category: "Invalid JSON format"})
                
        #         # Construct filters for each key-value pair in the JSON dictionary
        #         for key, value in category_dict.items():
        #             if value:
        #                 filters[f"{category}__{key}"] = value
                        
        qs = qs.filter(**filters)
        # JSON Field filter - end

        # Additional fields to filter - start
        all_keys = list(self.request.GET.keys())
        direct_fields = list(set(all_keys) -  set(non_db_fields)) #set(data_set_fields) -
        
        if search:
            qs = qs.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(email__icontains=search) | Q(mobile__icontains=search))
        
        # Filtering for direct fields
        for field in direct_fields:
            field_value = self.request.GET.get(field)
            if field_value is not None:
                # Special handling for fields if needed
                if field == "mobile" and field_value:
                    filters["mobile__contains"] = field_value
                elif field == "email" and field_value:
                    filters["email__contains"] = field_value
                elif field in ["is_superuser", "is_staff", "is_active",]:
                    filters[field] =  get_bool_value(field_value )
                elif field == "seen_customers":
                    field_value = field_value if field_value else '[]'
                    exclude["id__in"] = json.loads(field_value)
                else:
                    filters[field] = field_value
        # Additional fields to filter - end      
                      
        qs = qs.filter(**filters).exclude(**exclude)
        # print("Query : ", qs.query)

        # Add filter logic for non db fields - start
        
        return qs.order_by('-id')
    
    def post(self, request):
        user_obj = ""
        print("Receved User POST data ", self.request.data)
        required = ["mobile", "email", "first_name"]
        
        is_staff = self.request.data.get("is_staff", "0")
        is_verified = self.request.data.get("is_verified", "1")
        security_key = self.request.data.get("security_key", "")
        
        if security_key and len(security_key) !=6:
                return ResponseFunction(0, "Security Key must be 6 characters", {})
        
        if get_bool_value(is_staff) is False and get_bool_value(is_verified) is True:
            required.append("department")
        
        # if not request.POST.get("id", ""):
        #     required.extend(["password","confirm_password", ])
        
        validation_errors = ValidateRequest(required, self.request.data)

        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]['error'], {})
        else:
            print("Received required Fields")
            
        try:
            data = self.request.data.copy()
            
            if role := data.get("role"):
                if role == "" or role == "0" or role == 0:
                    data["role"] = None
            
            if get_bool_value(is_staff) is True:
                # Reset department for the user
                data['department'] = None
                
        except ValidationError as e:
            return ResponseFunction(0, str(e), {})

        try:
            
            id = self.request.POST.get("id", "")

            with transaction.atomic():
                if id:
                    is_security_key_exists = check_security_key_is_unique(security_key,user_id=id)
                    print("Edit: Is Security Key Unique ", is_security_key_exists)
                    if is_security_key_exists:
                        return ResponseFunction(0, "Security Key must be unique", {})
                    
                    user_qs = self.model.objects.filter(id=id)
                    if not user_qs.count():
                        return ResponseFunction(0, "UserDetail Not Found", {})
                    print("UserDetail Updating")
                    msg = "Data updated"
                    filtered_data = filter_valid_fields(self.model,data=data)
                    print("Filtered Data ", filtered_data)
                    serializer = UserSerializer(
                        user_qs.first(), filtered_data , partial=True,
                        context={'request': request}
                        )
                    if serializer.is_valid(raise_exception=True):

                        password = self.request.POST.get('password', '')
                        if password:
                            if self.request.data['password'] != self.request.data['confirm_password']:
                                # print("Password not matching")
                                # return ResponseFunction(False, "Try again", {})
                                raise Exception({"password": "Password and confirm password do not match."})
                            msg = "User details and password updated"
                            user_obj = serializer.save(
                                password=make_password(password))
                        else:
                            msg = "User details updated"
                            print("\n\n\nUser details updated")
                            user_obj = serializer.save()

                    else:
                        print("Serializer Errors ", serializer.errors)
                else:
                    is_security_key_exists = check_security_key_is_unique(security_key)
                    print("Add: Is Security Key Unique ", is_security_key_exists)
                    
                    if is_security_key_exists:
                        return ResponseFunction(0, "Security Key must be unique", {})
                    
                    data['username'] = data.get('email')
                    # temp_password = "123123" #generate_password(length=8, type="alphanumeric")
                    temp_password = generate_password(length=6, type="numeric")
                    data['is_temp_password'] = True
                    filtered_data = filter_valid_fields(self.model,data=data)
                    print("Filtered Data ", filtered_data)
                
                    serializer = UserSerializer(data=filtered_data, partial=True,context={'request': request})
                    if serializer.is_valid(raise_exception=True):
                        msg = f"Success, Temporary password sent to {data['email']}"
                        # if self.request.data['password'] != self.request.data['confirm_password']:
                        #     # print("Password not matching")
                        #     # return ResponseFunction(False, "Try again", {})
                        #     raise Exception({"password": "Password and confirm password do not match."})
                            
                            
                        # return ResponseFunction(False, "Try again", {})
                        user_obj = serializer.save(
                            password=make_password(temp_password))
                    email_payload = {
                        "to_email":data['email'],
                        # "to_email":"jasirmj@gmail.com",
                        "password":temp_password,
                        "subject":"JaysMetal - Account Created",
                        "body":f"Hi {data['first_name']} {data['last_name']}, your temporary password is "+temp_password
                    }
                    print("Adding new UserDetail",)
                    print("Email Payload ", email_payload)
                    
                    try:
                        django_send_email.delay(email_payload)
                    except Exception as e:
                        print(f"Celery Failed: Error sending email: {e}")
                        django_send_email(email_payload)


                token, created = Token.objects.get_or_create(user=user_obj)
                user_data = {}
                user_data['token'] = "Token "+str(token)
                user_data['data'] = UserAppSerializer(user_obj).data
          
                return ResponseFunction(True, msg, user_data)
        
        except ValidationError as e:
            # Return validation error messages if data is invalid
            msg = str(e)
            return ResponseFunction(0, msg, {})
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")

            # if user_obj:
            #     user_obj.delete()
            msg = str(e)
            return ResponseFunction(0, msg, {})

    def patch(self, request, *args, **kwargs):
        print("request data ", request.data)
        required = ["field_name"]
        validation_errors = ValidateRequest(required, request.data)
        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]['error'], {})
        else:
            print("Received required Fields for patch")
            
        try:
            user_id = self.request.user.id
            field_name = request.data.get("field_name")
            value = request.data.get("value")
            
            print("User ID: ", user_id)
            # Fetch the user
            user = self.model.objects.get(id=user_id)
            
            # Check if the field exists on the model
            if not hasattr(user, field_name):
                raise ValidationError({"error": f"Field '{field_name}' does not exist on the UserDetail model."})

            # For Foreignkeys
            if field_name == "organization":
                try:
                    value = int(value)  # Ensure value is an integer
                    organization = OrganizationModel.objects.get(id=value)
                    # setattr(user, field_name, organization)
                    user.organization = organization
                except OrganizationModel.DoesNotExist:
                    raise DefaultException( f"Organization with id {value} does not exist.")
            elif field_name == "department":
                try:
                    value = int(value)  # Ensure value is an integer
                    department = DepartmentModel.objects.get(id=value)
                    setattr(user, field_name, department)
                except DepartmentModel.DoesNotExist:
                    raise DefaultException( f"Department with id {value} does not exist.")
                
            else:
                # General field update
                setattr(user, field_name, value)

            user.save()
            
            user_data = UserSerializerSafe(user).data

            return ResponseFunction(1, f"Field '{field_name}' updated successfully.", user_data)
        except self.model.DoesNotExist:
            print("User not found.")
            return ResponseFunction(0, "User not found.", {})
        # except ValidationError as ve:
        #     print("Validation error:", ve.detail)
        #     return ResponseFunction(0, ve.detail, {})
        except Exception as e:
            print("Exception occurred:", str(e))
            return ResponseFunction(0, str(e), {})

    def delete(self, request):
        """
        Checks for superuser/staff/regular user permissions.

        Prevents superuser deletion by others.

        Prevents staff from deleting other staff or superusers.

        Regular users can only delete their own account, and only one at a time.
        """
        try:
            id = self.request.GET.get('id', "[]")
            if self.request.user.is_superuser:
                # Super Admin case
                if id == "all":
                    self.model.objects.all().exclude(is_superuser=True).delete()
                    return ResponseFunction(1, "Deleted all data")
                else:
                    ids = json.loads(id)
                    user_qs = self.model.objects.filter(id__in=ids)
                    
                    if user_qs.filter(is_superuser=True).exists():
                        return ResponseFunction(0, "You are not allowed to delete super admins, please contact Tech Support", {})
                    else:
                        user_qs.delete()
                
            elif self.request.user.is_staff:
                # Admin Staff case
                ids = json.loads(id)
                user_qs = self.model.objects.filter(id__in=ids)
                if user_qs.filter(Q(is_staff=True)| Q( is_superuser=True)).exists():
                    return ResponseFunction(0, "You are not allowed to delete other admins, please contact super admin", {})
                else:
                    user_qs.delete()
            else:
                # Regular User
                ids = json.loads(id)
                if len(ids) > 1:
                    return ResponseFunction(0, "You are not allowed to delete multiple data", {})
                else:
                    user_qs = self.model.objects.filter(id__in=ids)
                    if user_qs.filter(Q(is_superuser=True)| Q( is_staff=True)).exists():
                        return ResponseFunction(0, "You are not allowed to delete admins", {})
                    
                    if self.request.user.id == ids[0]:
                        user_qs.delete()
                    else:
                        return ResponseFunction(0, "You are not allowed to delete other users", {})
            return ResponseFunction(1, "Deleted data having id " + str(id), {})
                    
                        
        except json.JSONDecodeError:
            return ResponseFunction(0, "Invalid ID format", {})            
                
                

        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            msg = str(e)
            return ResponseFunction(0, msg, {})


class UserDepartmentHandler(APIView):
    model = UserDetail
    def post(self, request):
        """_summary_

        Args:
            user_id: to update the department of that user
            department_id_list: to update the department of the user
            operation: add or remove

        Returns:
            list_of_user departments
        """
        print(self.model.__name__, " Post ", request.data)
        required = ["user_id", "department_id_list", "operation"]
        validation_errors = ValidateRequest(required, request.data)
        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]["error"], {})
        
        operation = request.data.get("operation", "")
        user_id = request.data.get("user_id", "")
        department_id_list = json.loads(request.data.get("department_id_list", "[]"))
        try:
            print("Received required Fields", user_id, department_id_list, operation)
            
            user = self.model.objects.get(id=user_id)
            print("BEFORE : ",user.user_departments.all())
            if operation == "add":
                user.user_departments.add(*department_id_list)
            elif operation == "remove":
                user.user_departments.remove(*department_id_list)
            else:
                return ResponseFunction(0, "Invalid operation", {})
            print("After : ",user.user_departments.all())
            
            return ResponseFunction(1, "User Department updated", list(user.user_departments.values_list("id", flat=True)))
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            msg = str(e)
            return ResponseFunction(0, msg, {})

class LoginAPI(ObtainAuthToken):
    """
    API for user login
    """   

    def post(self, request, *args, **kwargs):
        error_message = ""

        keyword = self.request.data.get("keyword", "")
        
        is_valid = validate_request(request, ["keyword"])
        
        if get_bool_value(is_valid) is not True:
            return is_valid
        
        data = {}
        try:    
            if keyword == "email_login":
                error_message = "Invalid email or OTP"
                is_valid = validate_request(request, ["email", "otp"])
                print("email Is valid ",get_bool_value( is_valid))
                email = request.data.get("email", "")
                otp = request.data.get("otp", "")
                
                if get_bool_value(is_valid) is not True:    
                    return is_valid
                
                
                is_otp_verified = verify_otp(otp)
                
                if not is_otp_verified:
                    error_message = "Invalid OTP"
                    raise Exception(error_message)
                
                user = UserDetail.objects.get(email=email)  
                           
            elif keyword == "basic_auth":
                is_valid = validate_request(request, ["email", "password"])
                error_message = "Invalid email or password"
                if get_bool_value(is_valid) is not True:
                    return is_valid
                
                email = request.data.get("email", "")
                
                user = UserDetail.objects.get(email=email.lower())
                password = request.data.get("password", "")
                
                if not user.check_password(password):
                    raise Exception(error_message)
                
            elif keyword == "admin_login":
                is_valid = validate_request(request, ["username", "password"])
                error_message = "Invalid username or password"
                username = request.data.get("username", "")
                
                if get_bool_value(is_valid) is not True:
                    return is_valid
                
                # update on 15-Jul-2025 to allow login for clerk and shop
                user = UserDetail.objects.get(
                        Q(username=username) & 
                        (Q(is_staff=True) | Q(department__name__in=[CLERK_DEPARTMENT, SHOP_DEPARTMENT]))
                )
                
                password = request.data.get("password", "")
                
                if not user.check_password(password):
                    raise Exception(error_message)
                
            else:
                error_message = "Invalid keyword"
                raise Exception(error_message)
                # serializer = self.serializer_class(data=request.data,
                #                                     context={'request': request})

                # test = serializer.is_valid(raise_exception=True)
                # user = serializer.validated_data['user']

            token, created = Token.objects.get_or_create(user=user)

            data = {
                STATUS: True,
                'token': "Token "+token.key,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
            }


            data['user_data'] = UserAppSerializer(user).data

            # return Response(data)
            return ResponseFunction(1, "Login Success",data)
        
        except UserDetail.DoesNotExist:
            error_message = "No user found please register"
            print(f"{error_message} {printLineNo()}")
            return ResponseFunction(0, error_message, {})

        except Exception as e:
            
            print(f"Excepction occured {e} error at {printLineNo()}")
            msg = str(e) if error_message == "" else error_message
            return ResponseFunction(0, msg, {})
        
    
class SendOTPAPI(APIView):
    """
    API for sending OTP to email
    """

    def post(self, request):
        try:
            email = request.data.get("email", "")
            
            user = UserDetail.objects.get(email=email)
            is_valid = validate_request(request, ["email"])
            if get_bool_value(is_valid) is not True:
                return is_valid
            
            # Here you would implement the logic to send the OTP to the email
            # For now, we will just return a success message
            
            # send email 
            otp = generate_password(length=6, type="numeric")
            
            # Store OTP for email in redis with expiry
            redis_client.setex(email, 300, otp)  # 300 seconds = 5 minutes
            
            email_payload = {
                "to_email":email,
                "password":otp,
                "subject":"JaysMetal - Password Reset",
                "body":f"Your Password Reset OTP is {otp}, please do not share with anyone. If you did not request this, please ignore this email.",
            }
            print("Adding new UserDetail",)
            print("Email Payload ", email_payload)
            
            try:            
                django_send_email.delay(email_payload)
            except Exception as e:
                print(f"Celery Failed: Error sending email: {e}")
                django_send_email(email_payload)
            
            
            print(f"Sending OTP {otp} to {email}")
            
            return ResponseFunction(1, "OTP sent successfully", {"otp": otp})
        except UserDetail.DoesNotExist:
            error_message = "We couldn't find a user with that email address."
            return ResponseFunction(0, error_message, {})
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, str(e), {})


class ForgotPasswordAPI(APIView):
    """
    API for forgotpassword
    """
    def post(self, request):
        email = request.data.get("email", "")
        otp = request.data.get("otp", "")
        new_password = request.data.get("new_password", "")
        confirm_password = request.data.get("confirm_password", "")
        
        is_valid = validate_request(request, ["email", "otp","new_password", "confirm_password"])
        if get_bool_value(is_valid) is not True:
            return is_valid
        
        # simply change password for the user with the given email
        try:
            user = UserDetail.objects.get(email=email)
        
            # Here you would implement the logic to verify the OTP
    
            if new_password != confirm_password:
                return ResponseFunction(0, "New password and confirm password do not match", {})

            # if user.check_password(new_password):
            #     return ResponseFunction(0, "New password cannot be the same as old password", {})
            
            # Verify OTP with redis
            redis_otp = redis_client.get(email)
            print("Redis OTP ", redis_otp)
            
            if not redis_otp:
                return ResponseFunction(0, "Invalid OTP", {})
            
            if redis_otp != otp:
                return ResponseFunction(0, "Invalid OTP", {})
            
            # OTP verified — remove it from Redis
            redis_client.delete(email)
            
            # if not verify_otp(otp):
            #     return ResponseFunction(0, "Invalid OTP", {})
            
            # update user password with the new password
            user.set_password(new_password)
            user.save()
            return ResponseFunction(1, "Password changed successfully", {})
         
            
            # if len(new_password) < 6:
            #     return ResponseFunction(0, "New password must be at least 6 characters long", {})
            
            # if not any(char.isdigit() for char in new_password):
            #     return ResponseFunction(0, "New password must contain at least one digit", {})
            # if not any(char.isalpha() for char in new_password):
            #     return ResponseFunction(0, "New password must contain at least one letter", {})
            # if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for char in new_password):
            #     return ResponseFunction(0, "New password must contain at least one special character", {})
            
            
        except UserDetail.DoesNotExist:
            return ResponseFunction(0, "User with this email does not exist", {})
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, str(e), {})

    
class ChangePasswordAPI(ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    
    def post(self, request):
        try:
            user = request.user
            old_password = request.data.get("old_password", "")
            new_password = request.data.get("new_password", "")
            confirm_password = request.data.get("confirm_password", "")
            
            required = ["old_password", "new_password", "confirm_password"]
            
            is_valid = validate_request(request, required)
            if get_bool_value(is_valid) is not True:
                return is_valid
            
            
            if new_password != confirm_password:
                return ResponseFunction(0, "New password and confirm password do not match", {})
            
            if not user.check_password(old_password):
                return ResponseFunction(0, "Old password is incorrect", {})
            
            if old_password == new_password:
                return ResponseFunction(0, "New password cannot be the same as old password", {})
            
            # if len(new_password) < 6:
            #     return ResponseFunction(0, "New password must be at least 6 characters long", {})
            
            # if not any(char.isdigit() for char in new_password):
            #     return ResponseFunction(0, "New password must contain at least one digit", {})
            # if not any(char.isalpha() for char in new_password):
            #     return ResponseFunction(0, "New password must contain at least one letter", {})
            # if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for char in new_password):
            #     return ResponseFunction(0, "New password must contain at least one special character", {})
            
            user.set_password(new_password)
            user.is_temp_password = False
            user.save()
            
            return ResponseFunction(1, "Password changed successfully", {})
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, str(e), {})
    
    
class RoleAPI(ListAPIView):
  #  permission_classes = (IsAuthenticated,)
  #  authentication_classes = (TokenAuthentication,)
    model = Roles
    serializer_class = RoleSerializer
    
    def post(self, request):
        required = ["name",]
        validation_errors = ValidateRequest(required, request.data)

        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]["error"], {})
        else:
            print("Received required Fields")

        try:
            id = request.POST.get("id", "")

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

            if serializer.is_valid():
                serializer.save()
                return ResponseFunction(1, "Data saved", {})
            else:
                return ResponseFunction(0, serializer.errors, {})

        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, str(e), {})
   
    def get_queryset(self):
        print("Get RoleAPI")
        pagination = self.request.GET.get('pagination', '1')
        if pagination == '0':
            self.pagination_class = None
            self.serializer_class = RoleDropdownSerializer 
            
        qs = self.model.objects.all()

        # Additional fields to filter - start
        all_keys = list(self.request.GET.keys())
        direct_fields = list(set(all_keys) - set(non_db_fields))

        # Filtering for direct fields
        filters = {}
        for field in direct_fields:
            field_value = self.request.GET.get(field)
            if field_value is not None:
                filters[field] = field_value
        # Additional fields to filter - end      

        qs = qs.filter(**filters)
        print("Query : ", qs.query)

        return qs.order_by('-id')
    
class VerifySecurityKeyAPI(APIView):
    """
    API for verifying security key
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def post(self, request):
        try:
            security_key = request.data.get("security_key", "")
            
            is_valid = validate_request(request, ["security_key"])
            if get_bool_value(is_valid) is not True:
                return is_valid
            
            user_obj = UserDetail.objects.get(security_key=security_key)
            
            data = UserAppSerializer(user_obj).data
            
            if self.request.user.id == user_obj.id:
                data['is_own_account'] = True
            else:
                data['is_own_account'] = False
            
            return ResponseFunction(1, "Security Key verified successfully", data)
        except UserDetail.DoesNotExist:
            return ResponseFunction(0, "Invalid Security Key", {})
        except Exception as e:
            print(f"Excepction occured {e} error at {printLineNo()}")
            return ResponseFunction(0, str(e), {})
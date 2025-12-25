from rest_framework import serializers
from django_solvitize.utils.DynamicFieldsModel import DynamicFieldsModelSerializer
from user_app.models import Roles, UserDetail

        
class RoleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Roles
        fields = [
            "id",
            "name",
            "description",
            "permissions",
        ]

class RoleDropdownSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Roles
        fields = [
            "id",
            "name",
        ]
class UserSerializer(DynamicFieldsModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = UserDetail
        fields = [field.name for field in UserDetail._meta.get_fields() if field.concrete]# + ["media"]

class UserSerializerSafe(DynamicFieldsModelSerializer):

    class Meta:
        model = UserDetail
        exclude = [
            "password",
            "is_superuser",
            "is_staff",
            "last_login",
            "groups",
            "user_permissions",
            "is_active",
            "date_joined",
        ]   
        
class UserAppSerializer(DynamicFieldsModelSerializer):
    token = serializers.SerializerMethodField()
    role = RoleSerializer(read_only=True)
    
    class Meta:
        model = UserDetail
        fields = [
            "id",
            "email",
            "country_code",
            "mobile",
            "username",
            "first_name",
            "last_name",
            "organization",
            "department",
            "is_temp_password",
            "is_dev",
            "is_staff",
            "is_superuser",
            "is_verified",
            "notification_token",
            "token",
            "security_key",
            "profile_pic",
            "user_departments",
            "role",
        ]
    def get_token(self, obj):
        from rest_framework.authtoken.models import Token
        try:
            token, created = Token.objects.get_or_create(user=obj)
            return f"Token {token.key}"
        except Exception as e:
            print("Error on getting token for user",obj,e)
            return ""
        
        
class UserDetailDropdownSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = UserDetail
        fields = [
            "id",
            "first_name",
            "last_name",
            "profile_pic",
            "department",
            "user_departments",
        ]

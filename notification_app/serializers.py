# serializer
from rest_framework import serializers

from .models import NotificationModel, NotificationUserModel
from django_solvitize.utils.DynamicFieldsModel import DynamicFieldsModelSerializer


class NotificationUserSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = NotificationUserModel
        fields = '__all__'

class NotificationUserDropdownSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = NotificationUserModel
        fields = ('id', 'name')

class NotificationBaseSerializer(DynamicFieldsModelSerializer):
    
    class Meta:
        model = NotificationModel
        fields = '__all__'
        
class NotificationSerializer(DynamicFieldsModelSerializer):
    user_info = serializers.SerializerMethodField()
    class Meta:
        model = NotificationModel
        fields = [field.name for field in model._meta.get_fields() if field.concrete] + ["user_info"]
        
    def get_user_info(self, obj):
        request_user = self.context.get("request").user
        try:
            user_data_obj = NotificationUserModel.objects.get(notification=obj, user=request_user)
            return NotificationUserSerializer(user_data_obj).data
        except NotificationUserModel.DoesNotExist:
            return None


class NotificationDropdownSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = NotificationModel
        fields = ('id', 'name')

class NotificationUserSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = NotificationUserModel
        fields = '__all__'


# serializer
from department_app.utils import get_department_qs_common_method
from .models import ProjectGalleryModel, ProjectModel, ProjectUserModel, ProjectContact, ProjectTask
from django_solvitize.utils.DynamicFieldsModel import DynamicFieldsModelSerializer
from rest_framework import serializers

class ProjectContactSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ProjectContact
        fields = '__all__'

class ProjectUserSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ProjectUserModel
        fields = '__all__'


class ProjectSerializer(DynamicFieldsModelSerializer):
    contacts = serializers.SerializerMethodField()
    class Meta:
        model = ProjectModel
        fields = [field.name for field in ProjectModel._meta.get_fields() if field.concrete] + ["contacts"]

    def get_contacts(self, obj):
        response = []
        contact_obj = ProjectContact.objects.filter(project=obj)

        contact_data = ProjectContactSerializer(contact_obj, many=True).data
        response = contact_data
        return response
        

class ProjectWithUserSerializer(DynamicFieldsModelSerializer):
    project_users_info = serializers.SerializerMethodField()
    contacts = serializers.SerializerMethodField()
    class Meta:
        model = ProjectModel
        fields = [field.name for field in ProjectModel._meta.get_fields() if field.concrete] + ["project_users_info", "contacts"]  
        
    def get_project_users_info(self, obj):
        
        response = {}
        users_obj = ProjectUserModel.objects.filter(project=obj)
        
        user_data =  ProjectUserSerializer(users_obj, many=True).data
        response["users"] = user_data
        response["user_summary"] ={}
        
        # need to count user department wise
        for user in users_obj:
            if user.department in response["user_summary"].keys():
                response["user_summary"][user.department.name] += 1
            else:
                response["user_summary"][user.department.name] = 1
        return response

    def get_contacts(self, obj):
        response = []
        contact_obj = ProjectContact.objects.filter(project=obj)

        contact_data = ProjectContactSerializer(contact_obj, many=True).data
        response = contact_data
        return response
        
class ProjectDropdownSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ProjectModel
        fields = ('id', 'name')
        
class ProjectGallerySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ProjectGalleryModel
        fields = '__all__'
        
class ProjectReportSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ProjectModel
        fields = '__all__'

class ProjectContactDropdownSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ProjectContact
        fields = ('id', 'contact_name')

class ProjectTaskSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ProjectTask
        fields = '__all__'

class ProjectTaskDropdownSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ProjectTask
        fields = ('id', 'task_type')
    
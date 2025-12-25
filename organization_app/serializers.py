# serializer
from .models import OrganizationModel
from django_solvitize.utils.DynamicFieldsModel import DynamicFieldsModelSerializer

class OrganizationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = OrganizationModel
        fields = '__all__'

class OrganizationDropdownSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = OrganizationModel
        fields = ('id', 'name')
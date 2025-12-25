# serializer
from .models import DepartmentModel
from django_solvitize.utils.DynamicFieldsModel import DynamicFieldsModelSerializer

class DepartmentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = DepartmentModel
        fields = '__all__'

class DepartmentDropdownSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = DepartmentModel
        fields = ('id', 'name')
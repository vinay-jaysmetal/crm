
from django_solvitize.utils.DynamicFieldsModel import DynamicFieldsModelSerializer
from settings_app.models import *

class SettingsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = SettingsModel
        fields = "__all__"



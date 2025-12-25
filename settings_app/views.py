from django.shortcuts import render

# Create your views here.
from settings_app.models import *
from settings_app.serializers import SettingsSerializer
from django_solvitize.utils.GlobalFunctions import *
from django_solvitize.utils.GlobalImports import *

settings_list = [
    # SettingsModel(data_type="NUMBER", field_name='contact_24x7',
    #               value="PROVIDE_CUSTOMER_SUPPORT_NUMBER", description="Customer support 24x7", is_active=1),
    # SettingsModel(data_type="TEXT", field_name='onesignal_app_id', value="UPDATE ONE SIGNAL APP ID HERE",
    #               description="Used to send notification to the users", is_active=1),
    # SettingsModel(data_type="ARRAY", field_name='prescription_box_pin', value="679321,145512,512341",
    #               description="prescription box will be available at specified pin codes only", is_active=1),

    # SettingsModel(data_type="BOOLEAN", field_name='auto_order_refresh', value="false",
    #               description="if its true then automatically refresh order data", is_active=1),

    # SettingsModel(data_type="NUMBER", field_name='order_refresh_minutes', value="5",
    #               description="Automatically refresh order in specified minutes, recommended value 1 or more than 1", is_active=1),

    SettingsModel(data_type="TEXT", field_name='contact_support', value="UPDATE SUPPORT NUMBER HERE",
                  description="Used to track bugs", is_active=1),
    
    SettingsModel(data_type="TEXT", field_name='terms_and_conditions_link', value="UPDATE TERMS AND CONDITION LINK HERE",
                  description="Terms and Conditions", is_active=1),
    
    SettingsModel(data_type="TEXT", field_name='report_an_issue', value="UPDATE ISSUE REPORT LINK HERE",
                  description="Terms and Conditions", is_active=1),
    
    SettingsModel(data_type="TEXT", field_name='onesignal_app_id', value="UPDATE ONE SIGNAL APP ID HERE",
                  description="Used to send notification to the users", is_active=1),

    SettingsModel(data_type="TEXT", field_name='onesignal_rest_api_key', value="UPDATE ONE SIGNAL API KEY HERE",
                  description="Used to send notification to the users", is_active=1),

    SettingsModel(data_type="TEXT", field_name='min_app_version', value="1.0.0",
                  description="App will block if the app version below mentioned, format must be is X.X.X", is_active=1),
    SettingsModel(data_type="BOOLEAN", field_name='force_update_app_version', value="false",
                  description="App will force to update if the app version below mentioned", is_active=1),
    SettingsModel(data_type="BOOLEAN", field_name='allow_public_registration', value="true",
                  description="App will allow users to register if its true", is_active=1),


    # SettingsModel(data_type="TEXT", field_name='otp_provider', value="firebase",
    #               description="Provider which is used for OTP,eg : firebase or msg91", is_active=1),

    # SettingsModel(data_type="TEXT", field_name='razorpay_live_api_key', value="LIVE_API_KEY_HERE",
    #               description="Provider which is used for Online payment", is_active=1),
    # SettingsModel(data_type="TEXT", field_name='razorpay_live_api_secret', value="LIVE_API_SECRET_HERE",
    #               description="Provider which is used for Online payment", is_active=1),

    # SettingsModel(data_type="TEXT", field_name='razorpay_test_api_key', value="TEST_API_KEY_HERE",
    #               description="Provider which is used for Online payment", is_active=1),
    # SettingsModel(data_type="TEXT", field_name='razorpay_test_api_secret', value="TEST_API_SECRET_HERE",
    #               description="Provider which is used for Online payment", is_active=1),

    # SettingsModel(data_type="TEXT", field_name='online_payment_mode', value="live",
    #               description="online payment mode live or test", is_active=1),


    # SettingsModel(data_type="TEXT", field_name='msg91_auth_key', value="MSG91_AUTH_KEY_HERE",
    #               description="OTP provider Msg91 authorization key", is_active=1),

    # SettingsModel(data_type="TEXT", field_name='msg91_template_id', value="MSG91_TEMPLATE_ID_HERE",
    #               description="OTP provider Msg91 template id ", is_active=1),
]


def defaultSettings(snapshot):
    # NUMBER, TEXT, BOOLEAN, DATE, TIME, DATETIME

    new_settings = []
    for settings in settings_list:
        found = 0
        for snap in snapshot:
            if snap.field_name == settings.field_name:
                found = 1
                new_settings.append(snap)
                print("added old ", snap.field_name)
        if not found:
            print("added new ", settings.field_name)
            new_settings.append(settings)

    print("New items added ", len(new_settings))
    SettingsModel.objects.bulk_create(new_settings)
    return 1


class SettingsAPI(ListAPIView):

    serializer_class = SettingsSerializer
    # authentication_classes = (TokenAuthentication,)
    # permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        pagination = self.request.GET.get('pagination', '1')
        if pagination == '0':
            print("Pagination None")
            self.pagination_class = None

        # SettingsModel.objects.all().delete()
        field_name_list = json.loads(
            self.request.GET.get('field_name_list', "[]"))

        queryset = SettingsModel.objects.all()
        # return queryset
        print("QS Count ", queryset.count())
        print("Static list  Count ", len(settings_list))
        if queryset.count() != len(settings_list):
            print("Settings list count mismatch refreshing settings")
            snapshot = []

            for settings in SettingsModel.objects.all():
                snapshot.append(SettingsModel(field_name=settings.field_name, value=settings.value,
                                description=settings.description, data_type=settings.data_type, is_active=settings.is_active))

            SettingsModel.objects.all().delete()
            defaultSettings(snapshot)
        else:
            print("Settings are uptodate")
        qs = SettingsModel.objects.all()
        print("Settings Updated")

        if len(field_name_list):
            print("field_name list ")
            qs = qs.filter(field_name__in=field_name_list)

        return qs.order_by("-id")

    def post(self, request):
        print("data ", self.request.data)
        required = ["field_name", "value"]
        validation_errors = ValidateRequest(required, self.request.data)

        if len(validation_errors) > 0:
            return ResponseFunction(0, validation_errors[0]['error'], {})
        else:
            print("Receved required Fields")

        try:

            id = self.request.POST.get("id", "")
            field_name = request.POST.get('field_name', '')

            if field_name == "min_app_version":
                # version string validation
                validaiton_msg = "version format is invalid required format is X.Y.Z where X,Y,Z are numbers"
                version_list = request.data.get("value").split(".")
                if len(version_list) != 3:
                    return ResponseFunction(0, validaiton_msg, [])
                for x in version_list:
                    if not x.isnumeric():
                        return ResponseFunction(0, validaiton_msg, [])

            if id:
                print("Settings Updating")

                _qs = SettingsModel.objects.filter(id=id)
                if not _qs.count():
                    return ResponseFunction(0, "Settings Not Found", {})
                _obj = _qs.first()
                serializer = SettingsSerializer(
                    _obj, data=request.data, partial=True)
                msg = "Data updated"
            else:
                print("Adding new Settings")
                serializer = SettingsSerializer(
                    data=request.data, partial=True)
                msg = "Data saved"
            serializer.is_valid(raise_exception=True)

            obj = serializer.save()
            # print("Data id or object : ", obj.id)
            return ResponseFunction(1, msg, SettingsSerializer(SettingsModel.objects.all().order_by("-id"), many=True).data)
        except Exception as e:
            printLineNo()

            print("Excepction ", printLineNo(), " : ", e)
            # print("Excepction ",type(e))

            return ResponseFunction(0, f"Excepction occured {str(e)}", {})

    def put(self, request):

        ResponseFunction(0, "Not enabled", {})

        id = self.request.POST.get("id")
        if not id or id == "":
            return Response({
                STATUS: False,
                MESSAGE: "Required object id as id"
            })
        serializer = SettingsSerializer(SettingsModel.objects.filter(
            id=id).first(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ResponseFunction(1, "Data updated", {})

    def delete(self, request):
        try:
            id = self.request.GET.get('id', "[]")
            if id == "all":

                SettingsModel.objects.all().delete()
                return ResponseFunction(1, "Deleted all data", {})

            else:
                id = json.loads(id)
                # print(id)
                SettingsModel.objects.filter(id__in=id).delete()
                return ResponseFunction(1, "Deleted data having id " + str(id), {})

        except Exception as e:
            printLineNo()

            return Response(
                {
                    STATUS: False,
                    MESSAGE: str(e),
                    "line_no": printLineNo()
                }
            )



import json
from notification_app.models import NotificationModel, NotificationUserModel
from notification_app.serializers import NotificationBaseSerializer
from settings_app.models import SettingsModel
import requests
from jaysmetal_backend.celery import app

@app.task
def onesignal_push(
    lst_tokens, payload, type="normal", data=None, notification_id=None
):
    try:
        lst_tokens = list(set(lst_tokens)) # remove duplicates
        
        if len(lst_tokens) == 0:
            print("No tokens to send notification")
            return
        
        settings = SettingsModel.objects.filter(
            field_name__in=["onesignal_rest_api_key", "onesignal_app_id"]
        )
        settings_dict = {setting.field_name: setting.value for setting in settings}

        onesignal_rest_api_key = settings_dict.get("onesignal_rest_api_key")
        # onesignal_rest_api_key = "os_v2_app_byzwsx2fevf3fha7bansazfd5icwco6ke4ouzgvppchp4u5464lqhikkj677a624aakvk3465zjnu24zsvek5o44bote2d6dpt3z44i"
        onesignal_app_id = settings_dict.get("onesignal_app_id")

        # print("Settings Dict ", settings_dict)

        channel_id = "ONESIGNAL_CHANNEL_ID"

        header = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Basic {}".format(onesignal_rest_api_key),
        }

        notification_payload = {
            "app_id": onesignal_app_id,
            "include_subscription_ids": lst_tokens,
            "contents": {"en": payload.get('description', 'Jays Metal Description')},
            "headings": {
                "en": payload.get('title', 'Jays Metal')
            },
            "android_foreground": True,
            "persist": True,
            "android_visibility": 1,
            "priority": 10,
            "buttons": [
                {
                    "id": "view_now",
                    "text": "View Now",
                    "icon": "ic_menu_view"
                }
            ],
            
            # # 🔽 Android-specific image
            # "big_picture": payload.get("image", None),

            # # 🔽 iOS-specific image
            # "ios_attachments": {
            #     "id1": payload.get("image", None),
            # },

            # "appearance": [{"android_channel_id": ONE_SIGNAL_SHOP_ADMIN_CHANNEL_ID}]
        }
        
        if payload.get("image_url", None):
            # 🔽 Android-specific image
            notification_payload["big_picture"] = payload.get("image_url", None)
            
            # 🔽 iOS-specific image
            notification_payload["ios_attachments"] = {"id1": payload.get("image_url", None),}
            

        if type != "normal":
            notification_payload["android_channel_id"] = channel_id

        if data is not None:
            notification_payload["data"] = data

        print("Onesignal header is : ", header)
        print("Onesignal payload is : ", notification_payload)
        res = requests.post(
            "https://api.onesignal.com/notifications",
            headers=header,
            data=json.dumps(notification_payload),
        )
        print("Onesignal status code is : ", res.status_code)
        print("Onesignal response is : ", res.content)
        
        try:
            if notification_id:
                # Save the response data to the NotificationModel
                notificaiton_obj = NotificationModel.objects.get(id=notification_id)
                notificaiton_obj.request_data = notification_payload
                notificaiton_obj.response_data = res.json() if res else {}
                notificaiton_obj.save()
        except Exception as e:
            print("Error saving response data to NotificationModel: ", e)
        return res
    except Exception as e:
        print("Exception in onesignal_push ", e)
        pass


def send_notification_to_users(users_qs, title, description, image_url=None, notificaiton_type=1):
    """
    Send notification to a list of users.
    """
    if not users_qs:
        print("No users to send notification")
        return
    
    data = {
        "title": title,
        "description": description,
        "image_url": image_url,
        "notificaiton_type": notificaiton_type
    }
    
    notificaiton_obj = NotificationBaseSerializer(data=data)
    notificaiton_obj.is_valid(raise_exception=True)
    notificaiton_obj = notificaiton_obj.save()
    
    list_tokens = [user.notification_token for user in users_qs if user.notification_token]
    notification_user_objects = []
    for user in users_qs.distinct():
        
        if user.notification_token:
            list_tokens.append(user.notification_token)
            
        # Create NotificationModel instance
        notification_user_objects.append(
            NotificationUserModel(
                user=user,
                notification=notificaiton_obj
            )
        )
            
    # Bulk create NotificationUserModel
    NotificationUserModel.objects.bulk_create(notification_user_objects)
    
    # Send notification to users
    try:
        onesignal_push.delay(list_tokens, data, notification_id=notificaiton_obj.id)
    except Exception as e:
        print("Exception in sending notification to users: ", e)
        onesignal_push(list_tokens, data, notification_id=notificaiton_obj.id)
        

    
    

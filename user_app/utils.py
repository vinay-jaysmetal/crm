from user_app.models import UserDetail


def get_user_qs_project_based(project_obj):
    return UserDetail.objects.filter(
                project_users__project=project_obj
            ).distinct()

def check_security_key_is_unique(security_key,user_id=None):
    qs = UserDetail.objects.filter(security_key=security_key)
    if user_id:
        qs = qs.exclude(id=user_id)
    return qs.exists()
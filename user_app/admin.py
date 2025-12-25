from django.contrib import admin

# Register your models here.


from .models import UserDetail


class UserDetailAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "username",
        "email",
        "organization",
        "department",
        "is_staff",
        "is_verified",
        "is_active",
        "mobile",
        "user_token",
    ]
    readonly_fields = [
        "user_token",
        "created_at",
        "updated_at",
        "password",
        # "groups",
        # "user_permissions",
        # "subscribed_topics",
        # "read_notifications_ids",
    ]
    list_filter = ["organization", "department", "is_active"]

    def user_token(self, obj):
        try:
            return obj.auth_token.key  # Assumes a relation to auth_token
        except AttributeError:
            return None  # If there's no token associated, return None

    user_token.short_description = "User Token"  # Set column header name


admin.site.register(UserDetail, UserDetailAdmin)

from django.urls import path

from . import views

urlpatterns = [
    path('',views.UserAPI.as_view(), name='users'),
    path('department-handler/', views.UserDepartmentHandler.as_view(), name='users-update-departments'),
    path('login/',views.LoginAPI.as_view(), name='users-login'),
    path('sent-otp/',views.SendOTPAPI.as_view(), name='users-sent-otp'),
    path('forgot-password/',views.ForgotPasswordAPI.as_view(), name='users-forgot-password'),
    path('change-password/',views.ChangePasswordAPI.as_view(), name='users-change-password'),
    path('role/',views.RoleAPI.as_view(), name='users-role'),
    path('verify-security-key/',views.VerifySecurityKeyAPI.as_view(), name='users-verify-security-key'),
]
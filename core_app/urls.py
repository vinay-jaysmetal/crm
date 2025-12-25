
from django.urls import path

from . import views

urlpatterns = [
    path('',views.SplashAPIView.as_view()),
    path('dashboard/',views.AdminDashboard.as_view()),
]
from django.urls import path

from . import views

urlpatterns = [
    path('',views.SettingsAPI.as_view()),

]
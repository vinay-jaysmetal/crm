
from django.urls import path

from . import views

urlpatterns = [
    path('',views.DepartmentAPI.as_view()),
]

from django.urls import path

from . import views

urlpatterns = [
    path('fab-kg-report/',views.FabKgReportAPI.as_view()), 
    path('populate-fab-kg-report/',views.PopulateReportsAPI.as_view()), 

]
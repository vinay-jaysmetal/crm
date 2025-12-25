
from django.urls import path

from . import views

urlpatterns = [
    path('',views.FabricationListAPI.as_view()), # for creating and listing fabrication items
    path('upload/',views.FablistUploadViaFileView.as_view()), # for uploading fabrication items
    path('report/',views.FabReportListAPI.as_view()), # for creating and listing fabrication items
    path('report-users/',views.FabUsersReportAPI.as_view()), # for creating and listing fabrication items
    path('fab-kg-report/',views.NEWFabKgReportAPI.as_view()), # for creating and listing fabrication items
    path('fabitem-user-status/', views.FabricationStatusAPI.as_view(), name='fabitem-user-status'),  
    path('fabitem-user-status-bulk/', views.FabricationStatusUpdateBulkAPI.as_view(), name='fabitem-user-status-bulk'), 
    path("production-list/<int:project_id>/", views.download_fabrication_data_csv, name="production-list"),
]
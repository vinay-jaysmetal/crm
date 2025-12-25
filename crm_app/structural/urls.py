from django.urls import path
from .views import StructuralCompanyAPI, SalesRepDropdownAPI

urlpatterns = [
    # ----------------------------
    # Company / Customer APIs
    # ----------------------------
    # List all companies or create
    path('structural/clients/', StructuralCompanyAPI.as_view(), name='structural-company-list'),

    # Get by ID, update, delete
    path('structural/clients/<int:id>/', StructuralCompanyAPI.as_view(), name='structural-company-detail'),
    path('structural/sales-rep-dropdown/', SalesRepDropdownAPI.as_view(), name='structural-sales-rep-dropdown'),
]

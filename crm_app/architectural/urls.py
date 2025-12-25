from django.urls import path
from .views import ArchitecturalCompanyAPI

urlpatterns = [
    path("architectural/clients/", ArchitecturalCompanyAPI.as_view()),
    path("architectural/clients/<int:id>/", ArchitecturalCompanyAPI.as_view()),
]

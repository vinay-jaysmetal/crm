
from django.urls import path

from . import views
from . import views_gallery

urlpatterns = [
    path('',views.ProjectAPI.as_view()),
    path('users/',views.ProjectUserAPI.as_view()),
    path('gallery/',views_gallery.ProjectGalleryAPI.as_view()),
    path('contact/',views.ProjectContactAPI.as_view()),
    path('tasks/',views.ProjectTaskAPI.as_view()),
    path('bulk-update-tasks/',views.BulkUpdateProjectTaskAPI.as_view()),
] 
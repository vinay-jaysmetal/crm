
from django.urls import path

from . import views

urlpatterns = [
    path('',views.NotificationAPI.as_view()), # for creating and listing fabrication items
    path('mark-notification/',views.NotificationUserAPI.as_view()), # for creating and listing fabrication items
    # path('fabitem-user-status/', views.FabricationStatusAPI.as_view(), name='fabitem-user-status'),  # for getting user status of fabrication items
]
from django.urls import path
from .views import (
    StructuralCustomerAPI,
    SalesRepDropdownAPI,
    SharedCalendarAPIView,
    MyNotificationsAPIView,
    AcknowledgeReminderAPIView,
    MyRemindersAPIView,
    StructuralCategoriesAPIView
)

urlpatterns = [
    path('structural/clients/', StructuralCustomerAPI.as_view(), name='structural-company-list'),  # GET list / POST create
    path('structural/clients/<int:id>/', StructuralCustomerAPI.as_view(), name='structural-company-detail'),  # GET, PUT, DELETE
    path('structural/clients/category/', StructuralCategoriesAPIView.as_view(), name='structural-company-category'),
    path('structural/sales-rep-dropdown/', SalesRepDropdownAPI.as_view(), name='structural-sales-rep-dropdown'),
    path('structural/calendar/', SharedCalendarAPIView.as_view(), name='structural-shared-calendar'),
    path('structural/notifications/', MyNotificationsAPIView.as_view(), name='structural-my-notifications'),
    path('structural/reminders/<int:reminder_id>/acknowledge/', AcknowledgeReminderAPIView.as_view(), name='acknowledge-reminder'),
    path('structural/my-reminders/', MyRemindersAPIView.as_view(), name='my-reminders')
    
]

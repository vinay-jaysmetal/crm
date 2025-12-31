from django.urls import path
from .views import (
    StructuralCustomerAPI,
    SalesRepDropdownAPI,
    SharedCalendarAPIView,
    MyNotificationsAPIView,
    AcknowledgeReminderAPIView,
    MyRemindersAPIView,
<<<<<<< HEAD
    CompanyRemindersAPIView,
=======
>>>>>>> c5857fd16a47cbd7f5f16f6c8dd46cb2f0f30412
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
<<<<<<< HEAD
    path('structural/my-reminders/', MyRemindersAPIView.as_view(), name='my-reminders'),
    path('structural/companies/<int:company_id>/reminders/', CompanyRemindersAPIView.as_view(), name='company-reminders'),

=======
    path('structural/my-reminders/', MyRemindersAPIView.as_view(), name='my-reminders')
    
>>>>>>> c5857fd16a47cbd7f5f16f6c8dd46cb2f0f30412
]

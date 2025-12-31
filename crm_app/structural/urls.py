from django.urls import path
from .views import (
    StructuralCustomerAPI,
    SalesRepDropdownAPI,
    SharedCalendarAPIView,
    MyNotificationsAPIView,
    AcknowledgeReminderAPIView,
    MyRemindersAPIView,
    CompanyRemindersAPIView,
    StructuralCategoriesAPIView
)

urlpatterns = [
    # ----------------------------
    # Company / Client APIs
    # ----------------------------
    path('structural/clients/', StructuralCustomerAPI.as_view(), name='structural-company-list'),  # GET list / POST create
    path('structural/clients/<int:id>/', StructuralCustomerAPI.as_view(), name='structural-company-detail'),  # GET, PUT, DELETE

    # ----------------------------
    # Sales Rep Dropdown
    # ----------------------------
    path('structural/sales-rep-dropdown/', SalesRepDropdownAPI.as_view(), name='structural-sales-rep-dropdown'),

    # ----------------------------
    # Calendar APIs
    # ----------------------------
    path('structural/calendar/', SharedCalendarAPIView.as_view(), name='structural-shared-calendar'),

    # ----------------------------
    # Notification APIs
    # ----------------------------
    path('structural/notifications/', MyNotificationsAPIView.as_view(), name='structural-my-notifications'),

    # ----------------------------
    # Reminder Acknowledgement
    # ----------------------------
    path('structural/reminders/<int:reminder_id>/acknowledge/', AcknowledgeReminderAPIView.as_view(), name='acknowledge-reminder'),
    path('structural/my-reminders/', MyRemindersAPIView.as_view(), name='my-reminders'),
    path('structural/companies/<int:company_id>/reminders/', CompanyRemindersAPIView.as_view(), name='company-reminders'),
    path('structural/categories/', StructuralCategoriesAPIView.as_view(), name='structural-categories'),
]

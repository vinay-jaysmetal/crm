from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
import json
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from .utils import create_next_recurring_reminder

from django_solvitize.utils.GlobalImports import TokenAuthentication
from rest_framework.authentication import TokenAuthentication as DRFTokenAuthentication, get_authorization_header
from .models import StructuralCustomer, StructuralContact, StructuralNote, StructuralReminder, StructuralNotification, StructuralCalendarActivity
from .serializers import (
    StructuralCustomerSerializer,
    StructuralContactSerializer,
    StructuralNoteSerializer,
    StructuralReminderSerializer,
    StructuralNotificationSerializer,
    StructuralCalendarSerializer
)
from core_app.utils import ValidateRequest, get_bool_value
from django_solvitize.utils.GlobalFunctions import ResponseFunction, printLineNo

User = get_user_model()


class StructuralCustomerAPI(ListAPIView):
    serializer_class = StructuralCustomerSerializer
    queryset = StructuralCustomer.objects.all()

    # -----------------------
    # POST: Create new client
    # -----------------------
    def post(self, request, format=None):
        required = ["company_name", "added_by", "category"]
        validation_errors = ValidateRequest(required, request.data)
        if validation_errors:
            return ResponseFunction(0, validation_errors[0]['error'], {})

        contacts_data = request.data.pop("contacts", [])
        reminders_data = request.data.pop("reminders", [])
        notes_data = request.data.pop("notes", [])

        try:
            with transaction.atomic():
                serializer = self.serializer_class(data=request.data, context={'request': request})
                serializer.is_valid(raise_exception=True)
                company_obj = serializer.save()

                self._save_nested(company_obj, contacts_data, reminders_data, notes_data, request)

                data = self.serializer_class(company_obj).data
                return ResponseFunction(1, "Client created", data)

        except ValidationError as e:
            return ResponseFunction(0, str(e), request.data)
        except Exception as e:
            print(f"Exception occurred {e} at {printLineNo()}")
            return ResponseFunction(0, str(e), request.data)

    # -----------------------
    # PUT: Edit client by ID
    # -----------------------
    def put(self, request, id=None, format=None):
        if not id:
            return ResponseFunction(0, "ID is required for update", {})

        contacts_data = request.data.pop("contacts", [])
        reminders_data = request.data.pop("reminders", [])
        notes_data = request.data.pop("notes", [])

        try:
            with transaction.atomic():
                company_obj = get_object_or_404(StructuralCustomer, id=id)
                serializer = self.serializer_class(company_obj, data=request.data, partial=True, context={'request': request})
                serializer.is_valid(raise_exception=True)
                company_obj = serializer.save()

                self._save_nested(company_obj, contacts_data, reminders_data, notes_data, request)

                data = self.serializer_class(company_obj).data
                return ResponseFunction(1, "Client updated", data)

        except ValidationError as e:
            return ResponseFunction(0, str(e), request.data)
        except Exception as e:
            print(f"Exception occurred {e} at {printLineNo()}")
            return ResponseFunction(0, str(e), request.data)

    # -----------------------
    # GET: List all or retrieve by ID
    # -----------------------
    def get(self, request, id=None, *args, **kwargs):
        if id:  # Single client
            company_obj = get_object_or_404(StructuralCustomer, id=id)
            data = self.serializer_class(company_obj).data
            return ResponseFunction(1, "Client fetched successfully", data)
        else:  # List with pagination & filters
            qs = self.get_queryset()

            # Pagination using custom pagination class
            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(qs, many=True)
            return ResponseFunction(1, "Clients fetched successfully", serializer.data)

    # -----------------------
    # DELETE: Delete by ID or multiple IDs
    # -----------------------
    def delete(self, request, id=None):
        try:
            if id:
                StructuralCustomer.objects.filter(id=id).delete()
                return ResponseFunction(1, f"Deleted client with id {id}", {})

            ids = request.GET.get('id', '[]')
            if ids == "all":
                StructuralCustomer.objects.all().delete()
                return ResponseFunction(1, "Deleted all data")
            ids = json.loads(ids)
            if isinstance(ids, int):
                ids = [ids]
            StructuralCustomer.objects.filter(id__in=ids).delete()
            return ResponseFunction(1, f"Deleted data having id(s) {ids}", {})
        except Exception as e:
            print(f"Exception occurred {e} at {printLineNo()}")
            return ResponseFunction(0, str(e), {})

    # -----------------------
    # FILTERED Queryset
    # -----------------------
    

    def get_queryset(self):
            qs = StructuralCustomer.objects.all()

            # Query params
            is_dropdown = self.request.GET.get('is_dropdown', '0')
            exclude_id_list = json.loads(self.request.GET.get('exclude_id_list', '[]'))
            keyword = self.request.GET.get('search', '')  # search key
            category = self.request.GET.get('category')  # Existing / Potential
            lead_status = self.request.GET.get('lead_status')    # Hot / Warm / Cold
            project_status = self.request.GET.get('project_status')  # Hot / Warm / Cold

            # Non-model fields to exclude from filtering
            NON_DB_FIELDS = ['pagination', 'is_dropdown', 'exclude_id_list', 'page', 'search', 
                                'category', 'lead_status', 'project_status']

            # Handle dropdown: only id and company_name
            if is_dropdown == '1':
                qs = qs.only('id', 'company_name')

            # Apply exact filters from GET params
            filters = {}
            for field in self.request.GET.keys():
                if field in NON_DB_FIELDS:
                    continue

                value = self.request.GET.get(field)
                if value:
                    filters[field] = value

            qs = qs.filter(**filters)

            # Apply keyword search across multiple fields
            if keyword:
                qs = qs.filter(
                    Q(company_name__icontains=keyword) |
                    Q(email__icontains=keyword) |
                    Q(phone__icontains=keyword) |
                    Q(category__icontains=keyword) |
                    Q(existing_category__icontains=keyword) |
                    Q(potential_category__icontains=keyword) |
                    Q(address__icontains=keyword) |
                    Q(added_by__first_name__icontains=keyword) |
                    Q(added_by__last_name__icontains=keyword) |
                    Q(added_by__username__icontains=keyword)
                )

            # Apply category filters if provided
            if category:
                qs = qs.filter(category__iexact=category)
            if lead_status:
                qs = qs.filter(lead_status__iexact=lead_status)
            if project_status:
                qs = qs.filter(project_status__iexact=project_status)

            # Exclude IDs if provided
            if exclude_id_list:
                qs = qs.exclude(id__in=exclude_id_list)

            return qs.order_by('-id')



    # -----------------------
    # Paginate queryset correctly (use custom pagination)
    # -----------------------
    def paginate_queryset(self, queryset):
        if self.request.GET.get('pagination', '1') == '0':
            return None  # Disable pagination
        return super().paginate_queryset(queryset)

    # -----------------------
    # HELPER: Save Nested Contacts, Reminders, Notes
    # -----------------------
    def _save_nested(self, company_obj, contacts_data, reminders_data, notes_data, request):
        # Contacts
        for contact in contacts_data:
            contact_id = contact.get("id")
            if contact_id:
                contact_obj = get_object_or_404(StructuralContact, id=contact_id)
                contact_serializer = StructuralContactSerializer(contact_obj, data=contact, partial=True)
                contact_serializer.is_valid(raise_exception=True)
                contact_serializer.save()
            else:
                contact_serializer = StructuralContactSerializer(data=contact)
                contact_serializer.is_valid(raise_exception=True)
                contact_serializer.save(company=company_obj)

        # Reminders
        for reminder in reminders_data:
            reminder_id = reminder.get("id")
            assigned_to_id = reminder.get("assigned_to")
            assigned_to_user = get_object_or_404(User, id=assigned_to_id)

            if reminder_id:
                reminder_obj = get_object_or_404(StructuralReminder, id=reminder_id)
                reminder_serializer = StructuralReminderSerializer(
                    reminder_obj, data=reminder, partial=True
                )
                reminder_serializer.is_valid(raise_exception=True)
                reminder_obj = reminder_serializer.save(assigned_to=assigned_to_user)
            else:
                reminder_serializer = StructuralReminderSerializer(data=reminder)
                reminder_serializer.is_valid(raise_exception=True)
                reminder_obj = reminder_serializer.save(
                    company=company_obj,
                    assigned_to=assigned_to_user
                )

            # 🔔 CREATE NOTIFICATION
            StructuralNotification.objects.create(
            sales_person=assigned_to_user,
            company=company_obj,
            reminder=reminder_obj,
            message=f"Reminder to call {company_obj.company_name}"
            )

            # 📅 CREATE CALENDAR ENTRY
            # Get the latest note for this company
            latest_note = reminder_obj.company.notes.last()
            description = latest_note.note if latest_note else ""

            # Create calendar activity
            StructuralCalendarActivity.objects.create(
            company=company_obj,
            user=assigned_to_user,
            related_reminder=reminder_obj,
            title="Customer Follow-up",
            activity_date=reminder_obj.reminder_date,
            description=description  # use description here
            )


            # Notes
            added_by_id = request.data.get("added_by")
            added_by_user = get_object_or_404(User, id=added_by_id) if added_by_id else None
            for note in notes_data:
                note_content = note.get("content") or note.get("note")
                if note_content:
                    StructuralNote.objects.create(
                        company=company_obj,
                        note=note_content,
                        created_by=added_by_user
                    )


class SalesRepDropdownAPI(APIView):
    """
    Returns a list of active salespersons for dropdowns.
    """

    def get(self, request):
        try:
            sales_reps = User.objects.filter(role__name='Sales', is_active=True)
            data = [{"id": rep.id, "name": rep.get_full_name() or rep.username} for rep in sales_reps]
            return ResponseFunction(1, "Sales reps fetched successfully", data)

        except Exception as e:
            print(f"Exception occurred: {e}")
            return ResponseFunction(0, str(e), {})

# views.py

# class SharedCalendarAPIView(ListAPIView):
#     serializer_class = None  # manual response

#     def get(self, request):
#         qs = StructuralCalendarActivity.objects.select_related(
#             "company", "user", "related_reminder"
#         )

#         data = []
#         for obj in qs:
#             reminder = obj.related_reminder
#             data.append({
#                 "date": obj.activity_date,
#                 "title": obj.title,
#                 "company": {
#                     "id": obj.company.id,
#                     "name": obj.company.name,
#                 },
#                 "salesperson": {
#                     "id": obj.user.id,
#                     "name": obj.user.get_full_name(),
#                 },
#                 "reminder": {
#                     "id": reminder.id if reminder else None,
#                     "date": reminder.reminder_date if reminder else None,
#                     "frequency": reminder.frequency if reminder else None,
#                     "note": reminder.note if reminder else None,
#                     "completed": reminder.completed if reminder else None,
#                     "assigned_to": {
#                         "id": reminder.assigned_to.id,
#                         "name": reminder.assigned_to.get_full_name()
#                     } if reminder else None
#                 } if reminder else None,
#                 "notes": list(obj.company.notes.values("id", "note"))
#             })

#         return ResponseFunction(1, "Calendar fetched", data)

class SharedCalendarAPIView(ListAPIView):
    serializer_class = StructuralCalendarSerializer
    queryset = StructuralCalendarActivity.objects.all()

  
    
class MyNotificationsAPIView(ListAPIView):
    serializer_class = StructuralNotificationSerializer
    queryset=StructuralNotification.objects.all()

# def get_queryset(self):
#     return StructuralNotification.objects.filter(
#         user=self.request.user
#     ).order_by("-created_at")
    
        
class AcknowledgeReminderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, reminder_id):
        note = request.data.get("note")
        if not note:
            return ResponseFunction(0, "Notes are mandatory", {})

        reminder = get_object_or_404(StructuralReminder, id=reminder_id)

        # 🔒 Ownership check
        if reminder.assigned_to != request.user:
            return ResponseFunction(0, "You cannot complete this reminder", {})

        if reminder.status != 'Pending':
            return ResponseFunction(0, "Reminder is not pending", {})

        # Save note
        StructuralNote.objects.create(
            company=reminder.company,
            note=note,
            created_by=request.user
        )

        # Complete reminder
        reminder.status = 'Completed'
        reminder.completed_at = timezone.now()
        reminder.save()

        # Mark notification read
        StructuralNotification.objects.filter(
            reminder=reminder,
            sales_person=request.user
        ).update(read=True)

        # 🔁 Auto-create next reminder
        create_next_recurring_reminder(reminder)

        return ResponseFunction(1, "Reminder completed", {})

    

class BearerOrTokenAuthentication(DRFTokenAuthentication):
    def authenticate(self, request):
        raw = get_authorization_header(request)
        if not raw:
            return super().authenticate(request)
        header = raw.decode('utf-8').strip()
        lower = header.lower()
        token_value = None
        if lower.startswith('bearer '):
            token_value = header.split(' ', 1)[1].strip()
        elif lower.startswith('token '):
            token_value = header.split(' ', 1)[1].strip()
        if token_value:
            if token_value.lower().startswith('token '):
                token_value = token_value.split(' ', 1)[1].strip()
            request.META['HTTP_AUTHORIZATION'] = f'Token {token_value}'
        return super().authenticate(request)

class MyRemindersAPIView(ListAPIView):
    serializer_class = StructuralReminderSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (BearerOrTokenAuthentication,)

    def get_queryset(self):
        user = self.request.user

        # CEO can see all reminders (read-only)
        if hasattr(user, 'role') and user.role.name == 'CEO':
            return StructuralReminder.objects.all().order_by("reminder_date")

        # Sales Rep sees only their reminders
        return StructuralReminder.objects.filter(
            assigned_to=user
        ).order_by("reminder_date")


class CompanyRemindersAPIView(ListAPIView):
    serializer_class = StructuralReminderSerializer

    def get_queryset(self):
        company_id = self.kwargs.get("company_id")
        return StructuralReminder.objects.filter(
            company__id=company_id
        ).order_by("reminder_date")


class StructuralCategoriesAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = [
            {"name": "Existing", "sub_categories": [c[0] for c in StructuralCustomer.CATEGORY_CHOICES]},
            {"name": "Potential", "sub_categories": [c[0] for c in StructuralCustomer.CATEGORY_CHOICES]},
            {"name": "Lead Status", "sub_categories": [c[0] for c in StructuralCustomer.LEAD_STATUS_CHOICES]},
            {"name": "Project Status", "sub_categories": [c[0] for c in StructuralCustomer.PROJECT_STATUS_CHOICES]},
        ]
        return ResponseFunction(1, "Categories fetched", categories)


from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import ValidationError
import json
from django.contrib.auth import get_user_model
from rest_framework.views import APIView

from .models import StructuralCompany, StructuralContact, StructuralNote, StructuralReminder
from .serializers import (
    StructuralCompanySerializer,
    StructuralContactSerializer,
    StructuralNoteSerializer,
    StructuralReminderSerializer
)
from core_app.utils import ValidateRequest, get_bool_value
from django_solvitize.utils.GlobalFunctions import ResponseFunction, printLineNo

User = get_user_model()


class StructuralCompanyAPI(ListAPIView):
    serializer_class = StructuralCompanySerializer
    queryset = StructuralCompany.objects.all()

    # -----------------------
    # POST: Create new client
    # -----------------------
    def post(self, request, format=None):
        required = ["name", "added_by", "company_type"]
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
                company_obj = get_object_or_404(StructuralCompany, id=id)
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
            company_obj = get_object_or_404(StructuralCompany, id=id)
            data = self.serializer_class(company_obj).data
            return ResponseFunction(1, "Client fetched successfully", data)
        else:  # List with pagination & filters
            qs = self.get_queryset()
            
            # Pagination
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
                StructuralCompany.objects.filter(id=id).delete()
                return ResponseFunction(1, f"Deleted client with id {id}", {})

            ids = request.GET.get('id', '[]')
            if ids == "all":
                StructuralCompany.objects.all().delete()
                return ResponseFunction(1, "Deleted all data")
            ids = json.loads(ids)
            if isinstance(ids, int):
                ids = [ids]
            StructuralCompany.objects.filter(id__in=ids).delete()
            return ResponseFunction(1, f"Deleted data having id(s) {ids}", {})
        except Exception as e:
            print(f"Exception occurred {e} at {printLineNo()}")
            return ResponseFunction(0, str(e), {})

    # -----------------------
    # FILTERED Queryset
    # -----------------------
    def get_queryset(self):
        qs = StructuralCompany.objects.all()
        is_dropdown = self.request.GET.get('is_dropdown', '0')
        pagination = self.request.GET.get('pagination', '1')
        exclude_id_list = json.loads(self.request.GET.get('exclude_id_list', '[]'))

        if pagination == '0':
            self.pagination_class = None
            qs = qs  # disable pagination
        if is_dropdown == '1':
            qs = qs.only('id', 'name')

        filters = {}
        for field in self.request.GET.keys():
            value = self.request.GET.get(field)
            if value:
                if field == "name":
                    filters["name__icontains"] = value
                elif field in ["is_active"]:
                    filters["is_active"] = get_bool_value(value)
                else:
                    filters[field] = value

        if exclude_id_list:
            qs = qs.filter(**filters).exclude(id__in=exclude_id_list)
        else:
            qs = qs.filter(**filters)

        return qs.order_by('-id')

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
            assigned_to_user = get_object_or_404(User, id=assigned_to_id) if assigned_to_id else None

            if reminder_id:
                reminder_obj = get_object_or_404(StructuralReminder, id=reminder_id)
                reminder_serializer = StructuralReminderSerializer(reminder_obj, data=reminder, partial=True)
                reminder_serializer.is_valid(raise_exception=True)
                reminder_serializer.save(assigned_to=assigned_to_user)
            else:
                reminder_serializer = StructuralReminderSerializer(data=reminder)
                reminder_serializer.is_valid(raise_exception=True)
                reminder_serializer.save(company=company_obj, assigned_to=assigned_to_user)

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

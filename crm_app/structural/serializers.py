from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StructuralCustomer, StructuralContact, StructuralNote, StructuralReminder, StructuralNotification, StructuralCalendarActivity

User = get_user_model()


# ----------------------------
# Contact Serializer
# ----------------------------
class StructuralContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = StructuralContact
        fields = ('id', 'name', 'role', 'phone', 'email')
        read_only_fields = ('id',)


# ----------------------------
# Note Serializer
# ----------------------------
class StructuralNoteSerializer(serializers.ModelSerializer):
    created_by_detail = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = StructuralNote
        fields = ('id', 'note', 'created_by', 'created_by_detail')
        read_only_fields = ('id',)

    def get_created_by_detail(self, obj):
        if obj.created_by:
            return {"id": obj.created_by.id, "name": obj.created_by.get_full_name()}
        return None


# ----------------------------
# Reminder Serializer
# ----------------------------
class StructuralReminderSerializer(serializers.ModelSerializer):
    assigned_to_detail = serializers.SerializerMethodField(read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    notes = serializers.SerializerMethodField()
    class Meta:
        model = StructuralReminder
        fields = ('id', 'assigned_to', 'assigned_to_detail', 'reminder_date', 'frequency', 'status', 'notes')
        read_only_fields = ('id','status')

    def get_assigned_to_detail(self, obj):
        if obj.assigned_to:
            return {"id": obj.assigned_to.id, "name": obj.assigned_to.get_full_name()}
        return None

    def validate_assigned_to(self, value):
        if not value:
            raise serializers.ValidationError("assigned_to is required for each reminder.")
        return value

    def get_notes(self, obj):
        # Assuming Reminder has foreign key to Customer
        customer = obj.company
        last_note = customer.notes.last()  # Get last note for this customer
        if last_note:
            return {
                "id": last_note.id,
                "note": last_note.note,
                "created_by": last_note.created_by.username if last_note.created_by else None
            }
        return None

# ----------------------------
# Company Serializer
# ----------------------------
class StructuralCustomerSerializer(serializers.ModelSerializer):
    added_by_detail = serializers.SerializerMethodField(read_only=True)
    added_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    contacts = StructuralContactSerializer(many=True, required=False)
    reminders = StructuralReminderSerializer(many=True, required=False)
    notes = StructuralNoteSerializer(many=True, required=False)

    class Meta:
        model = StructuralCustomer
        fields = (
            'id',
            'company_name',
            'category',
            'existing_category',
            'potential_category',
            'email',
            'phone',
            'address',
            'added_by',
            'added_by_detail',
            'contacts',
            'reminders',
            'notes',
        )
        read_only_fields = ('id',)

    def get_added_by_detail(self, obj):
        if obj.added_by:
            return {"id": obj.added_by.id, "name": obj.added_by.get_full_name()}
        return None

    def create(self, validated_data):
        contacts_data = validated_data.pop('contacts', [])
        reminders_data = validated_data.pop('reminders', [])
        notes_data = validated_data.pop('notes', [])

        # Create company
        company = StructuralCustomer.objects.create(**validated_data)

        # Create contacts
        for contact_data in contacts_data:
            StructuralContact.objects.create(company=company, **contact_data)

        # Create reminders
        for reminder_data in reminders_data:
            assigned_to = reminder_data.pop('assigned_to')
            if not assigned_to:
                raise serializers.ValidationError("assigned_to is required for each reminder.")
            StructuralReminder.objects.create(company=company, assigned_to=assigned_to, **reminder_data)

        # Create notes
        for note_data in notes_data:
            note_content = note_data.get('note')
            if note_content:
                StructuralNote.objects.create(
                    company=company,
                    note=note_content,
                    created_by=validated_data.get('added_by')
                )

        return company

# serializers.py


class StructuralNotificationSerializer(serializers.ModelSerializer):
    company_detail = serializers.SerializerMethodField()
    reminder_detail = serializers.SerializerMethodField()
    is_read = serializers.BooleanField(source='read', read_only=True)
    notification_date = serializers.DateTimeField(source='created_at', read_only=True)
    class Meta:
        model = StructuralNotification
        fields = (
            "id",
            "message",
            "is_read",
            "company",
            "company_detail",
            "reminder",
            "reminder_detail",
            "notification_date",
        )

    def get_company_detail(self, obj):
        if not obj.company:
            return None
        return {
            "id": obj.company.id,
            "name": obj.company.company_name,
        }

    def get_reminder_detail(self, obj):
        r = obj.reminder
        if not r:
            return None

        # Fetch notes for this reminder via the customer
        notes = r.company.notes.values_list('note', flat=True)  # list of note texts

        return {
            "id": r.id,
            "date": r.reminder_date,
            "frequency": r.frequency,
            "notes": list(notes),  # include all notes
            "status": r.status,
            "assigned_to": {
                "id": r.assigned_to.id,
                "name": r.assigned_to.get_full_name(),
            } if r.assigned_to else None,
        }



class StructuralCalendarSerializer(serializers.ModelSerializer):
    # Mapping activity_date → date (FIXED)
    date = serializers.DateField(source="activity_date", read_only=True)

    company_detail = serializers.SerializerMethodField()
    salesperson = serializers.SerializerMethodField()
    reminder_detail = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()

    class Meta:
        model = StructuralCalendarActivity
        fields = (
            "date",
            "title",
            "company_detail",
            "salesperson",
            "reminder_detail",
            "notes",
        )

    def get_company_detail(self, obj):
        if not obj.company:
            return None
        return {
            "id": obj.company.id,
            "name": obj.company.company_name,
        }

    def get_salesperson(self, obj):
        if not obj.user:
            return None
        return {
            "id": obj.user.id,
            "name": obj.user.get_full_name(),
        }

    def get_reminder_detail(self, obj):
        r = obj.related_reminder
        if not r:
            return None

        notes = r.company.notes.values_list('note', flat=True)
        description = "\n".join(notes)


        return {
            "id": r.id,
            "date": r.reminder_date,
            "frequency": r.frequency,
            "status": r.status,
            "completed_at": r.completed_at,
            "notes": list(notes),  # add notes here
            "assigned_to": {
                "id": r.assigned_to.id,
                "name": r.assigned_to.get_full_name(),
            } if r.assigned_to else None,
        }



from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StructuralCompany, StructuralContact, StructuralNote, StructuralReminder

User = get_user_model()

# ----------------------------
# Nested Serializers
# ----------------------------
class StructuralContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = StructuralContact
        fields = ('id', 'name', 'role', 'phone', 'email')
        read_only_fields = ('id',)
        extra_kwargs = {
            'phone': {'required': False},
            'email': {'required': False},
        }


class StructuralNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StructuralNote
        fields = ('id', 'note', 'created_by')
        read_only_fields = ('id',)


class StructuralReminderSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = StructuralReminder
        fields = ('id', 'assigned_to', 'reminder_date', 'frequency', 'note', 'completed')
        read_only_fields = ('id',)


# ----------------------------
# Main StructuralCompany Serializer (Nested)
# ----------------------------
class StructuralCompanySerializer(serializers.ModelSerializer):
    contacts = StructuralContactSerializer(many=True, required=False)
    reminders = StructuralReminderSerializer(many=True, required=False)
    notes = StructuralNoteSerializer(many=True, required=False)

    class Meta:
        model = StructuralCompany
        fields = (
            'id',
            'name',
            'company_type',
            'existing_category',
            'potential_category',
            'email',
            'phone',
            'address',
            'added_by',
            'contacts',
            'reminders',
            'notes',
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'email': {'required': False},
            'phone': {'required': False},
        }

    def create(self, validated_data):
        contacts_data = validated_data.pop('contacts', [])
        reminders_data = validated_data.pop('reminders', [])
        notes_data = validated_data.pop('notes', [])

        company = StructuralCompany.objects.create(**validated_data)

        # -------------------
        # Create contacts
        # -------------------
        for contact_data in contacts_data:
            StructuralContact.objects.create(company=company, **contact_data)

        # -------------------
        # Create reminders
        # -------------------
        for reminder_data in reminders_data:
            assigned_to = reminder_data.pop('assigned_to')
            StructuralReminder.objects.create(company=company, assigned_to=assigned_to, **reminder_data)

        # -------------------
        # Create notes
        # -------------------
        for note_data in notes_data:
            note_content = note_data.get('note') or note_data.get('content')
            if note_content:
                StructuralNote.objects.create(company=company, note=note_content, created_by=validated_data.get('added_by'))

        return company

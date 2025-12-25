from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ArchitecturalCompany, ArchitecturalContact, ArchitecturalNote, ArchitecturalReminder

User = get_user_model()

# ----------------------------
# Nested Serializers
# ----------------------------
class ArchitecturalContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchitecturalContact
        fields = ('id', 'name', 'role', 'phone', 'email')
        read_only_fields = ('id',)
        extra_kwargs = {
            'phone': {'required': False},
            'email': {'required': False},
        }


class ArchitecturalNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchitecturalNote
        fields = ('id', 'note', 'created_by')
        read_only_fields = ('id',)


class ArchitecturalReminderSerializer(serializers.ModelSerializer):
    # Accept salesperson name instead of ID
    assigned_to = serializers.SlugRelatedField(
        queryset=User.objects.filter(role__name='Sales', is_active=True),
        slug_field='username'
    )

    class Meta:
        model = ArchitecturalReminder
        fields = ('id', 'assigned_to', 'reminder_date', 'frequency', 'note', 'completed')
        read_only_fields = ('id',)


# ----------------------------
# Main ArchitecturalCompany Serializer (Nested)
# ----------------------------
class ArchitecturalCompanySerializer(serializers.ModelSerializer):
    contacts = ArchitecturalContactSerializer(many=True, required=False)
    reminders = ArchitecturalReminderSerializer(many=True, required=False)
    notes = ArchitecturalNoteSerializer(many=True, required=False)

    # Accept salesperson name instead of ID
    added_by = serializers.SlugRelatedField(
        queryset=User.objects.filter(role__name='Sales', is_active=True),
        slug_field='username'
    )

    class Meta:
        model = ArchitecturalCompany
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

        company = ArchitecturalCompany.objects.create(**validated_data)

        # -------------------
        # Create contacts
        # -------------------
        for contact_data in contacts_data:
            ArchitecturalContact.objects.create(company=company, **contact_data)

        # -------------------
        # Create reminders
        # -------------------
        for reminder_data in reminders_data:
            assigned_to = reminder_data.pop('assigned_to')  # This is already a User instance
            ArchitecturalReminder.objects.create(company=company, assigned_to=assigned_to, **reminder_data)

        # -------------------
        # Create notes
        # -------------------
        for note_data in notes_data:
            note_content = note_data.get('note') or note_data.get('content')
            if note_content:
                ArchitecturalNote.objects.create(company=company, note=note_content, created_by=validated_data.get('added_by'))

        return company

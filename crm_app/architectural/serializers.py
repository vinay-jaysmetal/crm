from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ArchitecturalCompany, ArchitecturalContact, ArchitecturalNote, ArchitecturalReminder

User = get_user_model()


# ----------------------------
# Contact Serializer
# ----------------------------
class ArchitecturalContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchitecturalContact
        fields = ('id', 'name', 'role', 'phone', 'email')
        read_only_fields = ('id',)


# ----------------------------
# Note Serializer
# ----------------------------
class ArchitecturalNoteSerializer(serializers.ModelSerializer):
    created_by_detail = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ArchitecturalNote
        fields = ('id', 'note', 'created_by', 'created_by_detail')
        read_only_fields = ('id',)

    def get_created_by_detail(self, obj):
        if obj.created_by:
            return {"id": obj.created_by.id, "name": obj.created_by.get_full_name()}
        return None


# ----------------------------
# Reminder Serializer
# ----------------------------
class ArchitecturalReminderSerializer(serializers.ModelSerializer):
    assigned_to_detail = serializers.SerializerMethodField(read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ArchitecturalReminder
        fields = ('id', 'assigned_to', 'assigned_to_detail', 'reminder_date', 'frequency', 'note', 'completed')
        read_only_fields = ('id',)

    def get_assigned_to_detail(self, obj):
        if obj.assigned_to:
            return {"id": obj.assigned_to.id, "name": obj.assigned_to.get_full_name()}
        return None

    def validate_assigned_to(self, value):
        if not value:
            raise serializers.ValidationError("assigned_to is required for each reminder.")
        return value


# ----------------------------
# Company Serializer
# ----------------------------
class ArchitecturalCompanySerializer(serializers.ModelSerializer):
    added_by_detail = serializers.SerializerMethodField(read_only=True)
    added_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    contacts = ArchitecturalContactSerializer(many=True, required=False)
    reminders = ArchitecturalReminderSerializer(many=True, required=False)
    notes = ArchitecturalNoteSerializer(many=True, required=False)

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
        company = ArchitecturalCompany.objects.create(**validated_data)

        # Create contacts
        for contact_data in contacts_data:
            ArchitecturalContact.objects.create(company=company, **contact_data)

        # Create reminders
        for reminder_data in reminders_data:
            assigned_to = reminder_data.pop('assigned_to')
            if not assigned_to:
                raise serializers.ValidationError("assigned_to is required for each reminder.")
            ArchitecturalReminder.objects.create(company=company, assigned_to=assigned_to, **reminder_data)

        # Create notes
        for note_data in notes_data:
            note_content = note_data.get('note')
            if note_content:
                ArchitecturalNote.objects.create(
                    company=company,
                    note=note_content,
                    created_by=validated_data.get('added_by')
                )

        return company

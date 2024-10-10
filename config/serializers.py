from rest_framework import serializers
from .models import TwilioConfig
from assistant.models import Assistant

class AssistantSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assistant
        fields = ['id', 'name']  # Include only the fields you need

class TwilioConfigurationSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    assistants = AssistantSimpleSerializer(many=True, read_only=True)  # Use nested serializer

    class Meta:
        model = TwilioConfig
        fields = '__all__'
        read_only_fields = ('created_by', 'created_on', 'updated_on')

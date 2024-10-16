from rest_framework import serializers
from .models import Client

class ClientSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    call_status_display = serializers.CharField(source='get_call_status_display', read_only=True)

    class Meta:
        model = Client
        fields = [
            'id', 'name', 'phone_number', 'call_status', 'call_status_display', 'is_called', 
            'created_by', 'created_on', 'updated_on'
        ]
        read_only_fields = ['created_by', 'created_on', 'updated_on']

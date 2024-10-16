
from django.contrib import admin
from .models import Client



class ClientAdmin(admin.ModelAdmin):
    
    list_display = (
        'name', 
        'phone_number', 
        'call_status_display', 
        'is_called', 
        'created_by', 
        'created_on', 
        'updated_on'
    )
    
    search_fields = (
        'name', 
        'phone_number', 
        'created_by__username'
    )
    
    list_filter = (
        'call_status', 
        'is_called', 
        'created_by', 
        'created_on'
    )
    
    readonly_fields = (
        'created_on', 
        'updated_on'
    )
    
    ordering = ('-created_on',)

    def call_status_display(self, obj):
        return obj.get_call_status_display()
    call_status_display.short_description = 'Call Status'

admin.site.register(Client, ClientAdmin)

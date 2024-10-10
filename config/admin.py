from django.contrib import admin
from .models import TwilioConfig
from django import forms
from django.utils.html import format_html

class TwilioConfigAdmin(admin.ModelAdmin):
    list_display = (
        'label', 'twilio_no', 'account_sid', 'display_created_by',
        'created_on', 'updated_on'
    )
    search_fields = ('label', 'twilio_no', 'account_sid', 'created_by__username')
    readonly_fields = ('created_on', 'updated_on', 'created_by_display')
    ordering = ('-created_on',)
    list_filter = ('created_on', 'created_by')

    fieldsets = (
        (None, {
            'fields': ('label', 'twilio_no')
        }),
        ('Credentials', {
            'fields': ('account_sid', 'auth_token')
        }),
        ('Owner', {
            'fields': ('created_by_display',)
        }),
        ('Timestamps', {
            'fields': ('created_on', 'updated_on')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:
            readonly += ['auth_token']
            # Only allow superusers to change 'created_by'
            if not request.user.is_superuser:
                readonly += ['created_by_display']
        return readonly

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'auth_token':
            kwargs['widget'] = forms.PasswordInput(render_value=True)
        return super().formfield_for_dbfield(db_field, **kwargs)
    
    def save_model(self, request, obj, form, change):
        if not change:
            # Set created_by on creation
            obj.created_by = request.user
        obj.save()
    
    def created_by_display(self, obj):
        if obj.created_by:
            return obj.created_by.username
        return '-'
    created_by_display.short_description = 'Created By'

    def display_created_by(self, obj):
        return obj.created_by.username if obj.created_by else '-'
    display_created_by.short_description = 'Created By'

admin.site.register(TwilioConfig, TwilioConfigAdmin)

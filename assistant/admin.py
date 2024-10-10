from django.contrib import admin
from .models import Assistant

class AssistantAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'is_publish', 'created_by', 'max_tokens', 'idle_timeout',
        'max_idle_messages', 'created_on', 'updated_on'
    )
    list_filter = ('is_publish', 'created_by', 'created_on')
    search_fields = ('name', 'prompt', 'greeting_message', 'idle_message', 'created_by__username')
    ordering = ('-created_on',)
    readonly_fields = ('created_on', 'updated_on', 'created_by_display')
    actions = ['publish_assistants', 'unpublish_assistants']

    fieldsets = (
        (None, {
            'fields': ('name', 'is_publish', 'created_by_display')
        }),
        ('Content', {
            'fields': ('prompt', 'greeting_message', 'idle_message')
        }),
        ('Settings', {
            'fields': ('max_tokens', 'idle_timeout', 'max_idle_messages')
        }),
        ('Timestamps', {
            'fields': ('created_on', 'updated_on')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if not request.user.is_superuser:
            readonly.append('created_by_display')
        return readonly

    def created_by_display(self, obj):
        return obj.created_by.username if obj.created_by else '-'
    created_by_display.short_description = 'Created By'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.save()

    def publish_assistants(self, request, queryset):
        queryset.update(is_publish=True)
        self.message_user(request, "Selected assistants have been published.")
    publish_assistants.short_description = "Publish selected assistants"

    def unpublish_assistants(self, request, queryset):
        queryset.update(is_publish=False)
        self.message_user(request, "Selected assistants have been unpublished.")
    unpublish_assistants.short_description = "Unpublish selected assistants"

admin.site.register(Assistant, AssistantAdmin)

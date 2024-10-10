from django.contrib import admin
from .models import Call, Log

class LogInline(admin.TabularInline):
    model = Log
    extra = 0
    readonly_fields = ('created_on', 'updated_on')
    fields = ('user', 'message', 'time')
    can_delete = False  # Prevent deletion from inline

class CallAdmin(admin.ModelAdmin):
    list_display = ('session_name', 'assistant', 'created_by', 'number_of_logs', 'created_on', 'updated_on')
    search_fields = ('session_name', 'assistant__name', 'created_by__username')
    list_filter = ('assistant', 'created_by', 'created_on')
    readonly_fields = ('created_on', 'updated_on')
    ordering = ('-created_on',)
    inlines = [LogInline]

    def number_of_logs(self, obj):
        return obj.logs.count()
    number_of_logs.short_description = 'Number of Logs'

admin.site.register(Call, CallAdmin)

class LogAdmin(admin.ModelAdmin):
    list_display = ('call', 'user', 'message', 'created_on')
    search_fields = ('call__session_name', 'user', 'message')
    list_filter = ('user', 'created_on')
    readonly_fields = ('created_on', 'updated_on')
    ordering = ('-created_on',)

admin.site.register(Log, LogAdmin)

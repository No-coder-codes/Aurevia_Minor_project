from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['short_content', 'project', 'sender', 'timestamp']
    list_filter = ['timestamp', 'project']
    search_fields = ['content', 'sender__username', 'project__title']
    raw_id_fields = ['project', 'sender']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp']

    @admin.display(description='Message')
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

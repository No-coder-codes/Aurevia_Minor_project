from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target_content_type', 'target_object_id', 'timestamp']
    list_filter = ['target_content_type', 'timestamp']
    search_fields = ['user__username', 'action', 'target_content_type']
    raw_id_fields = ['user']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    readonly_fields = ['user', 'action', 'target_content_type', 'target_object_id', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

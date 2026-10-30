from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'manager', 'start_date', 'end_date', 'member_count', 'created_at']
    list_filter = ['status', 'start_date', 'end_date', 'created_at']
    search_fields = ['title', 'description', 'manager__username', 'manager__email']
    raw_id_fields = ['manager']
    filter_horizontal = ['members']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

    @admin.display(description='Members')
    def member_count(self, obj):
        return obj.members.count()

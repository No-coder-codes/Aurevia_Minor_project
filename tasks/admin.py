from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assignee', 'status', 'priority', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'due_date', 'created_at']
    search_fields = ['title', 'description', 'assignee__username', 'project__title']
    raw_id_fields = ['project', 'assignee']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status', 'priority']

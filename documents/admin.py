from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'task', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at', 'project']
    search_fields = ['title', 'description', 'uploaded_by__username', 'project__title']
    raw_id_fields = ['project', 'task', 'uploaded_by']
    ordering = ['-uploaded_at']
    date_hierarchy = 'uploaded_at'
    readonly_fields = ['uploaded_at']

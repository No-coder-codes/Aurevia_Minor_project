from django.db import models
from django.conf import settings

class ActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    workspace = models.ForeignKey('core.Workspace', on_delete=models.CASCADE, related_name='activity_logs', null=True, blank=True)
    action = models.CharField(max_length=255)
    target_content_type = models.CharField(max_length=100, blank=True) # e.g., 'Project', 'Task'
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"

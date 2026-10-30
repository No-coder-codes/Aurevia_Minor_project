from django.db import models
from django.conf import settings

class Document(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='documents')
    task = models.ForeignKey('tasks.Task', on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='project_documents/')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

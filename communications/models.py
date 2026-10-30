from django.db import models
from django.conf import settings

class Message(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}..."

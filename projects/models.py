from django.db import models
from django.conf import settings
from django.utils import timezone

class Project(models.Model):
    STATUS_CHOICES = (
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    )

    title = models.CharField(max_length=200)
    workspace = models.ForeignKey('core.Workspace', on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='managed_projects'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='joined_projects',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def progress_percentage(self):
        """Calculate project progress based on completed tasks or status."""
        if self.status == 'completed':
            return 100
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.tasks.filter(status='done').count()
        return round((completed_tasks / total_tasks) * 100)

    @property
    def remaining_days(self):
        """Calculate remaining days until deadline."""
        if self.end_date:
            delta = self.end_date - timezone.now().date()
            return max(0, delta.days)
        return None

    def __str__(self):
        return self.title

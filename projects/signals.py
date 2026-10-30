from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Project


@receiver(post_save, sender=Project)
def log_project_activity(sender, instance, created, **kwargs):
    """Log when a project is created or updated."""
    from history.models import ActivityLog

    # Skip if no manager is set (can't log without a user)
    if not instance.manager:
        return

    if created:
        action = f'Created project "{instance.title}"'
    else:
        action = f'Updated project "{instance.title}" (status: {instance.get_status_display()})'

    ActivityLog.objects.create(
        user=instance.manager,
        action=action,
        target_content_type='Project',
        target_object_id=instance.pk,
    )

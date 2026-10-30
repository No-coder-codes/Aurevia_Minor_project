from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message


@receiver(post_save, sender=Message)
def log_message_posted(sender, instance, created, **kwargs):
    """Log when a new message is posted."""
    from history.models import ActivityLog

    if not created:
        return  # Only log new messages

    ActivityLog.objects.create(
        user=instance.sender,
        action=f'Posted a message in project "{instance.project.title}"',
        target_content_type='Message',
        target_object_id=instance.pk,
    )

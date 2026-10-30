from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Document


@receiver(post_save, sender=Document)
def log_document_upload(sender, instance, created, **kwargs):
    """Log when a new document is uploaded."""
    from history.models import ActivityLog

    if not created:
        return  # Only log new uploads, not edits

    ActivityLog.objects.create(
        user=instance.uploaded_by,
        action=f'Uploaded document "{instance.title}" to project "{instance.project.title}"',
        target_content_type='Document',
        target_object_id=instance.pk,
    )

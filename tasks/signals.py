from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Task
from core.models import Notification
from history.models import ActivityLog

@receiver(pre_save, sender=Task)
def track_task_changes(sender, instance, **kwargs):
    """Store the original assignee and status before saving to detect changes."""
    if instance.pk:
        try:
            original = Task.objects.get(pk=instance.pk)
            instance._original_assignee = original.assignee
            instance._original_status = original.status
        except Task.DoesNotExist:
            instance._original_assignee = None
            instance._original_status = None
    else:
        instance._original_assignee = None
        instance._original_status = None

@receiver(post_save, sender=Task)
def handle_task_notifications_and_logs(sender, instance, created, **kwargs):
    """Send notifications and log activity when a task is created or updated."""
    # 1. Activity Log
    if created:
        action_text = f'Created task "{instance.title}" in project "{instance.project.title}"'
    else:
        action_text = f'Updated task "{instance.title}" (status: {instance.get_status_display()}, priority: {instance.get_priority_display()})'

    # Use the project manager or assignee for logging user if possible
    log_user = instance.project.manager or instance.assignee
    if log_user:
        ActivityLog.objects.create(
            user=log_user,
            action=action_text,
            target_content_type='Task',
            target_object_id=instance.pk,
        )

    # 2. Assignment Notification
    original_assignee = getattr(instance, '_original_assignee', None)
    if instance.assignee and (created or original_assignee != instance.assignee):
        Notification.objects.create(
            recipient=instance.assignee,
            sender=instance.project.manager,
            message=f'You have been assigned to task "{instance.title}" in project "{instance.project.title}".',
            notif_type='task',
            link=f'/tasks/'
        )

    # 3. Status Change Notification (to project manager when moved to review or done)
    original_status = getattr(instance, '_original_status', None)
    if instance.project.manager and original_status != instance.status:
        if instance.status in ['review', 'done']:
            sender_user = instance.assignee or log_user
            message_text = f'Task "{instance.title}" has been moved to "{instance.get_status_display()}" by {sender_user.username if sender_user else "a team member"}.'
            Notification.objects.create(
                recipient=instance.project.manager,
                sender=sender_user,
                message=message_text,
                notif_type='task',
                link=f'/tasks/'
            )

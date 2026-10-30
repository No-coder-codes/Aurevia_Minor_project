from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = (
        ('director', 'Director'),
        ('project_manager', 'Project Manager'),
        ('team_member', 'Team Member'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='team_member')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Organization(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Workspace(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_workspaces', null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='workspaces')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class WorkspaceMembership(models.Model):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('project_manager', 'Project Manager'),
        ('team_member', 'Team Member'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workspace_memberships')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='team_member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'workspace')

    def __str__(self):
        return f"{self.user.username} in {self.workspace.name} ({self.role})"



class Notification(models.Model):
    TYPES = (
        ('task', 'Task Assignment'),
        ('team', 'Team Update'),
        ('removal', 'Removal Request'),
        ('system', 'System Alert'),
    )
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    notif_type = models.CharField(max_length=20, choices=TYPES, default='system')
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class RemovalRequest(models.Model):
    STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='removal_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_removals')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Remove {self.target_user.username} (by {self.requester.username})"

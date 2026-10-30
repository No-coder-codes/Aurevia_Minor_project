from rest_framework import viewsets, permissions, exceptions
from django.db.models import Q
from .models import Message
from .serializers import MessageSerializer
from core.views import get_active_workspace

class MessagePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        active_workspace = get_active_workspace(request)
        if not active_workspace:
            return False
        # Project must belong to active workspace
        if not obj.project or obj.project.workspace != active_workspace:
            return False
        # User must be a member of the project or manager or director
        user = request.user
        if user.role == 'director':
            return True
        if obj.project.manager == user:
            return True
        return user in obj.project.members.all()

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [MessagePermission]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Message.objects.none()
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            return Message.objects.none()

        # Messages within active workspace where user has access to project
        qs = Message.objects.filter(project__workspace=active_workspace)
        if user.role != 'director':
            qs = qs.filter(Q(project__manager=user) | Q(project__members=user)).distinct()

        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def perform_create(self, serializer):
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            raise exceptions.PermissionDenied("An active workspace is required to send messages.")
        project = serializer.validated_data.get('project')
        if not project or project.workspace != active_workspace:
            raise exceptions.PermissionDenied("Cannot attach message to a project outside your active workspace.")
        user = self.request.user
        if user.role != 'director' and project.manager != user and user not in project.members.all():
            raise exceptions.PermissionDenied("You must be a member of the project to post messages.")
        serializer.save(sender=user)

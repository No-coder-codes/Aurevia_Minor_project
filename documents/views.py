from rest_framework import viewsets, permissions, exceptions
from .models import Document
from .serializers import DocumentSerializer
from core.views import get_active_workspace
from projects.models import Project

class DocumentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        active_workspace = get_active_workspace(request)
        if not active_workspace:
            return False
        # Document project must belong to the user's active workspace
        if not obj.project or obj.project.workspace != active_workspace:
            return False
        # If user is team_member, can only update/delete if uploaded_by them
        if request.user.role == 'team_member' and request.method not in permissions.SAFE_METHODS:
            return obj.uploaded_by == request.user
        return True

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [DocumentPermission]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Document.objects.none()
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            return Document.objects.none()

        qs = Document.objects.filter(project__workspace=active_workspace)
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs

    def perform_create(self, serializer):
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            raise exceptions.PermissionDenied("An active workspace is required to create documents.")
        project = serializer.validated_data.get('project')
        if project and project.workspace != active_workspace:
            raise exceptions.PermissionDenied("Cannot attach document to a project outside your active workspace.")
        serializer.save(uploaded_by=self.request.user)

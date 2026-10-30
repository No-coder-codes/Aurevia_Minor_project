from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models # Ensure this import is present for models.Q if needed elsewhere
from .models import Project
from .serializers import ProjectSerializer, ProjectDetailSerializer

class ProjectPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if obj.workspace and not request.user.workspace_memberships.filter(workspace=obj.workspace).exists():
            return False
        if request.user.role == 'director':
            return True
        if request.user.role == 'project_manager':
            return obj.manager == request.user
        # Team members can view but not edit
        if request.method in permissions.SAFE_METHODS:
            return request.user in obj.members.all()
        return False

class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [ProjectPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'start_date', 'end_date']

    def get_queryset(self):
        user = self.request.user
        from core.views import get_active_workspace
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            return Project.objects.none()
        if user.role == 'director':
            return Project.objects.filter(workspace=active_workspace)
        elif user.role == 'project_manager':
            return Project.objects.filter(workspace=active_workspace, manager=user)
        else:
            return Project.objects.filter(workspace=active_workspace, members=user)

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return ProjectDetailSerializer
        return ProjectSerializer

    def perform_create(self, serializer):
        from core.views import get_active_workspace
        from rest_framework import exceptions
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            raise exceptions.PermissionDenied("An active workspace is required to create a project.")
        serializer.save(manager=self.request.user, workspace=active_workspace)

    @action(detail=True, methods=['get'])
    def risk_analysis(self, request, pk=None):
        project = self.get_object()
        from core.services.risk_engine import RiskEngine
        engine = RiskEngine()
        analysis = engine.analyze_project(project)
        
        risks_data = []
        for r in analysis.risks:
            risks_data.append({
                'rule_code': r.rule_code,
                'severity': r.severity,
                'score_addition': r.score_addition,
                'description': r.description,
                'target_id': r.target_id
            })
            
        return Response({
            'project_id': project.id,
            'score': analysis.score,
            'status': analysis.status,
            'risks': risks_data,
            'recommendations': analysis.recommendations
        })

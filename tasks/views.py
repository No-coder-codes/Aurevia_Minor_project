from rest_framework import viewsets, permissions
from django.db.models import Q
from .models import Task, SubTask, TaskComment, TimeLog
from .serializers import TaskSerializer, SubTaskSerializer, TaskCommentSerializer, TimeLogSerializer
from .permissions import TaskPermission


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [TaskPermission]

    def get_queryset(self):
        user = self.request.user
        from core.views import get_active_workspace
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            return Task.objects.none()

        # Director sees all tasks in active workspace
        if user.role == 'director':
            qs = Task.objects.filter(project__workspace=active_workspace)

        # Project Manager sees tasks from projects they manage in active workspace
        elif user.role == 'project_manager':
            qs = Task.objects.filter(project__workspace=active_workspace, project__manager=user)

        # Team Member sees tasks assigned to them OR in projects they belong to in active workspace
        else:
            qs = Task.objects.filter(
                project__workspace=active_workspace
            ).filter(
                Q(assignee=user) | Q(project__members=user)
            ).distinct()

        # Optional: filter by project query param
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)

        return qs

    def perform_create(self, serializer):
        from core.views import get_active_workspace
        from rest_framework import exceptions
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            raise exceptions.PermissionDenied("An active workspace is required to create a task.")
        project = serializer.validated_data.get('project')
        if not project or project.workspace != active_workspace:
            raise exceptions.PermissionDenied("Cannot attach a task to a project outside your active workspace.")
        serializer.save()

class SubTaskPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        from core.views import get_active_workspace
        active_workspace = get_active_workspace(request)
        if not active_workspace:
            return False
        return bool(obj.task and obj.task.project and obj.task.project.workspace == active_workspace)

class SubTaskViewSet(viewsets.ModelViewSet):
    serializer_class = SubTaskSerializer
    permission_classes = [SubTaskPermission]

    def get_queryset(self):
        from core.views import get_active_workspace
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            return SubTask.objects.none()
        return SubTask.objects.filter(task__project__workspace=active_workspace)

    def perform_create(self, serializer):
        from core.views import get_active_workspace
        from rest_framework import exceptions
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            raise exceptions.PermissionDenied("An active workspace is required.")
        task = serializer.validated_data.get('task')
        if not task or not task.project or task.project.workspace != active_workspace:
            raise exceptions.PermissionDenied("Cannot attach subtask to a task outside your active workspace.")
        serializer.save()

class TaskCommentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        from core.views import get_active_workspace
        active_workspace = get_active_workspace(request)
        if not active_workspace:
            return False
        if not (obj.task and obj.task.project and obj.task.project.workspace == active_workspace):
            return False
        if request.method not in permissions.SAFE_METHODS:
            return obj.user == request.user or request.user.role in ['director', 'project_manager']
        return True

class TaskCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TaskCommentSerializer
    permission_classes = [TaskCommentPermission]

    def get_queryset(self):
        from core.views import get_active_workspace
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            return TaskComment.objects.none()
        return TaskComment.objects.filter(task__project__workspace=active_workspace)

    def perform_create(self, serializer):
        from core.views import get_active_workspace
        from rest_framework import exceptions
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            raise exceptions.PermissionDenied("An active workspace is required.")
        task = serializer.validated_data.get('task')
        if not task or not task.project or task.project.workspace != active_workspace:
            raise exceptions.PermissionDenied("Cannot comment on a task outside your active workspace.")
        serializer.save(user=self.request.user)

class TimeLogPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        from core.views import get_active_workspace
        active_workspace = get_active_workspace(request)
        if not active_workspace:
            return False
        if not (obj.task and obj.task.project and obj.task.project.workspace == active_workspace):
            return False
        if request.method not in permissions.SAFE_METHODS:
            return obj.user == request.user or request.user.role in ['director', 'project_manager']
        return True

class TimeLogViewSet(viewsets.ModelViewSet):
    serializer_class = TimeLogSerializer
    permission_classes = [TimeLogPermission]

    def get_queryset(self):
        from core.views import get_active_workspace
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            return TimeLog.objects.none()
        return TimeLog.objects.filter(task__project__workspace=active_workspace)

    def perform_create(self, serializer):
        from core.views import get_active_workspace
        from rest_framework import exceptions
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            raise exceptions.PermissionDenied("An active workspace is required.")
        task = serializer.validated_data.get('task')
        if not task or not task.project or task.project.workspace != active_workspace:
            raise exceptions.PermissionDenied("Cannot log time on a task outside your active workspace.")
        serializer.save(user=self.request.user)

from rest_framework import permissions


class TaskPermission(permissions.BasePermission):
    """
    Role-based permission for Tasks:
    - Director: full access to all tasks
    - Project Manager: access tasks of projects they manage
    - Team Member: access only tasks assigned to them
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Must belong to user's workspace
        if hasattr(obj, 'project') and obj.project and obj.project.workspace:
            if not user.workspace_memberships.filter(workspace=obj.project.workspace).exists():
                return False

        # Directors can do anything within their workspace
        if user.role == 'director':
            return True

        # Project Managers can access tasks in their managed projects
        if user.role == 'project_manager':
            return obj.project.manager == user

        # Team Members can only access tasks assigned to them
        if user.role == 'team_member':
            # Allow read access if they are a project member
            if request.method in permissions.SAFE_METHODS:
                return obj.assignee == user or user in obj.project.members.all()
            # Write access only on their own assigned tasks
            return obj.assignee == user

        return False

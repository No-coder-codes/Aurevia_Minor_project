from rest_framework import permissions

class IsDirector(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'director'

class IsProjectManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 'project_manager' or request.user.role == 'director')

class IsTeamMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

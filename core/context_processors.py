from .models import Notification

def notifications_processor(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False)
        return {
            'unread_notifications': unread_notifications,
            'unread_notifications_count': unread_notifications.count()
        }
    return {
        'unread_notifications': [],
        'unread_notifications_count': 0
    }

def workspace_context(request):
    from .models import Workspace, WorkspaceMembership
    if not request.user.is_authenticated:
        return {
            'active_workspace': None,
            'active_role': None,
            'available_workspaces': []
        }

    # Fetch memberships
    memberships = WorkspaceMembership.objects.filter(user=request.user).select_related('workspace')
    available_workspaces = [m.workspace for m in memberships]

    active_workspace_id = request.session.get('active_workspace_id')
    active_workspace = None
    active_role = None

    if active_workspace_id:
        membership = next((m for m in memberships if m.workspace.id == int(active_workspace_id)), None)
        if membership:
            active_workspace = membership.workspace
            active_role = membership.role

    if not active_workspace and memberships.exists():
        first_membership = memberships.first()
        active_workspace = first_membership.workspace
        active_role = first_membership.role
        request.session['active_workspace_id'] = active_workspace.id

    return {
        'active_workspace': active_workspace,
        'active_role': active_role,
        'available_workspaces': available_workspaces
    }

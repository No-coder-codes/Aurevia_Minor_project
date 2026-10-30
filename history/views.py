from rest_framework import viewsets, permissions
from .models import ActivityLog
from .serializers import ActivityLogSerializer
from core.views import get_active_workspace

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ActivityLog.objects.none()
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            return ActivityLog.objects.none()

        qs = ActivityLog.objects.filter(workspace=active_workspace)
        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs

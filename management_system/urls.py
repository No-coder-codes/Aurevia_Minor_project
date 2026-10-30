from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from core.views import (
    DashboardView, ProjectDetailView, TaskListView, 
    ActivityLogView, FileListView, DashboardAPIView, 
    UserViewSet, ProjectCreateView, ProjectUpdateView,
    ProjectDeleteView, TaskCreateView, TaskUpdateView,
    TaskDeleteView, TeamListView, UserCreateView,
    RequestRemovalView, ReviewRemovalView, MarkAllNotificationsReadView,
    ExportProjectDataView, SwitchWorkspaceView, WorkspaceSettingsView, WorkspaceCreateView
)
from projects.views import ProjectViewSet
from tasks.views import TaskViewSet, SubTaskViewSet, TaskCommentViewSet, TimeLogViewSet
from communications.views import MessageViewSet
from documents.views import DocumentViewSet
from history.views import ActivityLogViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'subtasks', SubTaskViewSet, basename='subtask')
router.register(r'comments', TaskCommentViewSet, basename='comment')
router.register(r'timelogs', TimeLogViewSet, basename='timelog')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'history', ActivityLogViewSet, basename='activitylog')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Frontend Views
    path('', DashboardView.as_view(), name='dashboard'),
    path('projects/add/', ProjectCreateView.as_view(), name='project_add'),
    path('projects/<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<int:pk>/edit/', ProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<int:pk>/delete/', ProjectDeleteView.as_view(), name='project_delete'),
    path('tasks/', TaskListView.as_view(), name='task_list'),
    path('tasks/add/', TaskCreateView.as_view(), name='task_add'),
    path('tasks/<int:pk>/edit/', TaskUpdateView.as_view(), name='task_edit'),
    path('tasks/<int:pk>/delete/', TaskDeleteView.as_view(), name='task_delete'),
    path('history/', ActivityLogView.as_view(), name='activity_history'),
    path('files/', FileListView.as_view(), name='file_list'),
    
    # Team Management
    path('team/', TeamListView.as_view(), name='team_list'),
    path('team/add/', UserCreateView.as_view(), name='user_add'),
    path('team/remove/<int:pk>/', RequestRemovalView.as_view(), name='request_removal'),
    path('team/review/<int:pk>/', ReviewRemovalView.as_view(), name='review_removal'),
    
    path('notifications/read-all/', MarkAllNotificationsReadView.as_view(), name='mark_all_read'),
    path('export/projects/', ExportProjectDataView.as_view(), name='export_projects'),
    
    # Workspaces
    path('workspaces/switch/<int:workspace_id>/', SwitchWorkspaceView.as_view(), name='switch_workspace'),
    path('workspace/settings/', WorkspaceSettingsView.as_view(), name='workspace_settings'),
    path('workspace/create/', WorkspaceCreateView.as_view(), name='workspace_create'),
    path('college/', include('academics.urls', namespace='academics')),

    # Auth
    path('', include('django.contrib.auth.urls')),
    
    # API Routes
    path('api/', include(router.urls)),
    path('api/dashboard/', DashboardAPIView.as_view(), name='api_dashboard'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

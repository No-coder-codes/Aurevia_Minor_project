import csv
from django.http import StreamingHttpResponse
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import User, Notification, RemovalRequest
from .forms import HierarchicalUserCreationForm, ProjectForm, TaskForm, WorkspaceForm, DocumentForm
from projects.models import Project
from tasks.models import Task
from history.models import ActivityLog
from documents.models import Document
from .serializers import UserSerializer
from .models import Organization, Workspace, WorkspaceMembership

def get_active_workspace(request):
    if not request.user.is_authenticated:
        return None

    # 1. Query parameter override (if requesting a specific workspace)
    explicit_id = None
    if hasattr(request, 'query_params'):
        explicit_id = request.query_params.get('workspace') or request.query_params.get('workspace_id')
    elif hasattr(request, 'GET'):
        explicit_id = request.GET.get('workspace') or request.GET.get('workspace_id')

    if explicit_id:
        membership = WorkspaceMembership.objects.filter(
            user=request.user,
            workspace_id=explicit_id
        ).select_related('workspace').first()
        return membership.workspace if membership else None

    # 2. Check active session
    session = getattr(request, 'session', None)
    if session:
        active_id = session.get('active_workspace_id')
        if active_id:
            membership = WorkspaceMembership.objects.filter(
                user=request.user,
                workspace_id=active_id
            ).select_related('workspace').first()
            if membership:
                return membership.workspace

    # 3. Fallback to user's first available workspace membership
    membership = WorkspaceMembership.objects.filter(
        user=request.user
    ).select_related('workspace').first()
    if membership:
        if session:
            session['active_workspace_id'] = membership.workspace.id
        return membership.workspace

    # No workspace membership found - return None safely without side-effects
    return None

class WorkspaceIsolatedMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        active_workspace = get_active_workspace(self.request)
        if active_workspace:
            if hasattr(queryset.model, 'workspace'):
                return queryset.filter(workspace=active_workspace)
            elif hasattr(queryset.model, 'project'):
                return queryset.filter(project__workspace=active_workspace)
        return queryset.none()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            return User.objects.filter(id=user.id)
        # Users sharing the active workspace
        return User.objects.filter(workspace_memberships__workspace=active_workspace).distinct()

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        active_workspace = get_active_workspace(request)
        # Cannot modify/delete foreign workspace users
        if active_workspace:
            if not obj.workspace_memberships.filter(workspace=active_workspace).exists():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You do not have permission to access users outside your workspace.")


class DashboardAPIView(APIView):
    """
    Dashboard endpoint returning project stats, task stats,
    overdue tasks, and recent activity — strictly filtered by active workspace and user role.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from projects.models import Project
        from tasks.models import Task
        from history.models import ActivityLog
        from history.serializers import ActivityLogSerializer

        user = request.user
        today = timezone.now().date()
        active_workspace = get_active_workspace(request)

        if not active_workspace:
            return Response({
                'total_projects': 0,
                'completed_projects': 0,
                'pending_projects': 0,
                'total_tasks': 0,
                'completed_tasks': 0,
                'overdue_tasks': 0,
                'recent_activity': [],
            })

        # --- Role-based querysets within active workspace ---
        if user.role == 'director':
            projects = Project.objects.filter(workspace=active_workspace)
            tasks = Task.objects.filter(project__workspace=active_workspace)
            logs = ActivityLog.objects.filter(workspace=active_workspace)
        elif user.role == 'project_manager':
            projects = Project.objects.filter(workspace=active_workspace, manager=user)
            tasks = Task.objects.filter(project__workspace=active_workspace, project__manager=user)
            logs = ActivityLog.objects.filter(workspace=active_workspace, user=user)
        else:
            projects = Project.objects.filter(workspace=active_workspace, members=user)
            tasks = Task.objects.filter(project__workspace=active_workspace, assignee=user)
            logs = ActivityLog.objects.filter(workspace=active_workspace, user=user)

        # --- Project stats ---
        total_projects = projects.count()
        completed_projects = projects.filter(status='completed').count()
        pending_projects = total_projects - completed_projects

        # --- Task stats ---
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='done').count()
        overdue_tasks = tasks.exclude(status='done').filter(
            due_date__lt=today
        ).count()

        # --- Recent activity ---
        recent_logs = logs[:10]
        recent_activity = ActivityLogSerializer(recent_logs, many=True).data

        return Response({
            'total_projects': total_projects,
            'completed_projects': completed_projects,
            'pending_projects': pending_projects,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'overdue_tasks': overdue_tasks,
            'recent_activity': recent_activity,
        })

# --- Template Views ---

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Role-based project filtering
        if user.role == 'director':
            projects = Project.objects.all()
        elif user.role == 'project_manager':
            projects = Project.objects.filter(manager=user)
        else:
            projects = Project.objects.filter(members=user)

        # Enforce Workspace Isolation
        active_workspace = get_active_workspace(self.request)
        if active_workspace:
            projects = projects.filter(workspace=active_workspace)
        else:
            projects = Project.objects.none()

        # Handle status filtering from sidebar
        status_filter = self.request.GET.get('status')
        dashboard_title = "Aurevia Dashboard"
        
        if status_filter:
            projects = projects.filter(status=status_filter)
            dashboard_title = f"{status_filter.capitalize()} Projects"
            
        context['total_projects'] = projects.count()
        context['active_projects'] = projects.filter(status='active').count()
        context['completed_projects'] = projects.filter(status='completed').count()
        context['pending_projects'] = projects.exclude(status='completed').count()
        
        from django.utils import timezone
        today = timezone.now().date()
        context['overdue_projects'] = projects.exclude(status='completed').filter(end_date__lt=today).count()
        
        context['dashboard_title'] = dashboard_title
        context['current_status'] = status_filter
        
        # Risk Engine Integration
        from core.services.risk_engine import RiskEngine
        engine = RiskEngine()
        projects_prefetch = list(projects.select_related('manager').prefetch_related(
            'tasks',
            'tasks__assignee',
            'tasks__dependencies'
        ))
        analyses = engine.analyze_multiple_projects(projects_prefetch, today=today)
        for a in analyses:
            a.project.risk_analysis = a
            
        context['projects'] = [a.project for a in analyses]
        context['off_track_count'] = sum(1 for a in analyses if a.status == 'off_track')
        context['at_risk_count'] = sum(1 for a in analyses if a.status == 'at_risk')
        
        top_recommendations = []
        for a in analyses:
            if a.status in ['at_risk', 'off_track'] and a.recommendations:
                for r in a.recommendations:
                    top_recommendations.append(f"{a.project.title}: {r}")
        context['top_recommendations'] = top_recommendations[:5]
        
        # Recent activity
        if active_workspace:
            context['recent_activities'] = ActivityLog.objects.filter(workspace=active_workspace)[:10]
            try:
                from academics.models import (
                    School,
                    AcademicDepartment,
                    AdministrativeDepartment,
                    Programme,
                    StudentProfile,
                    AdmissionsApplication,
                )
                context['college_stats'] = {
                    'schools_count': School.objects.filter(workspace=active_workspace).count(),
                    'academic_depts_count': AcademicDepartment.objects.filter(school__workspace=active_workspace).count(),
                    'programmes_count': Programme.objects.filter(department__school__workspace=active_workspace).count(),
                    'students_count': StudentProfile.objects.filter(programme__department__school__workspace=active_workspace).count(),
                    'hostels_count': AdministrativeDepartment.objects.filter(workspace=active_workspace, category__in=['boys_hostel', 'girls_hostel']).count(),
                    'admissions_pending': AdmissionsApplication.objects.filter(workspace=active_workspace, status__in=['submitted', 'admin_review', 'academic_review']).count(),
                }
            except Exception:
                context['college_stats'] = None
        else:
            context['recent_activities'] = ActivityLog.objects.none()
            context['college_stats'] = None
        
        return context

class ProjectDetailView(WorkspaceIsolatedMixin, LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Single project risk analysis
        from core.services.risk_engine import RiskEngine
        engine = RiskEngine()
        analysis = engine.analyze_project(project)
        context['risk_analysis'] = analysis
        return context

class TaskListView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'director':
            qs = Task.objects.all()
        elif user.role == 'project_manager':
            qs = Task.objects.filter(project__manager=user)
        else:
            qs = Task.objects.filter(assignee=user)
        
        active_workspace = get_active_workspace(self.request)
        if active_workspace:
            qs = qs.filter(project__workspace=active_workspace)
        else:
            qs = qs.none()
        return qs

class ActivityLogView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    model = ActivityLog
    template_name = 'history/activity.html'
    context_object_name = 'logs'

class FileListView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    model = Document
    template_name = 'documents/files.html'
    context_object_name = 'files'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_workspace = get_active_workspace(self.request)
        if 'form' not in context:
            context['form'] = DocumentForm(workspace=active_workspace)
        if active_workspace:
            context['user_files'] = Document.objects.filter(uploaded_by=self.request.user, project__workspace=active_workspace)
        else:
            context['user_files'] = Document.objects.none()
        return context

    def post(self, request, *args, **kwargs):
        active_workspace = get_active_workspace(request)
        form = DocumentForm(request.POST, request.FILES, workspace=active_workspace)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, f"Document '{document.title}' uploaded successfully.")
            return redirect('file_list')
        
        self.object_list = self.get_queryset()
        context = self.get_context_data(object_list=self.object_list, form=form)
        context['show_modal'] = True
        return self.render_to_response(context)

# --- Create/Update Views ---

class ProjectAccessMixin(UserPassesTestMixin):
    def test_func(self):
        project = self.get_object()
        user = self.request.user
        if user.role == 'director':
            return True
        if user.role == 'project_manager':
            return project.manager == user
        return False

class TaskAccessMixin(UserPassesTestMixin):
    def test_func(self):
        task = self.get_object()
        user = self.request.user
        if user.role == 'director':
            return True
        if user.role == 'project_manager':
            return task.project.manager == user
        if user.role == 'team_member':
            return task.assignee == user
        return False

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    template_name = 'projects/project_form.html'
    form_class = ProjectForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.manager = self.request.user
        active_workspace = get_active_workspace(self.request)
        if active_workspace:
            form.instance.workspace = active_workspace
        response = super().form_valid(form)
        messages.success(self.request, f"Project '{self.object.title}' was successfully created.")
        return response

class ProjectUpdateView(WorkspaceIsolatedMixin, LoginRequiredMixin, ProjectAccessMixin, UpdateView):
    model = Project
    template_name = 'projects/project_form.html'
    form_class = ProjectForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Project '{self.object.title}' was updated successfully.")
        return response

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    template_name = 'tasks/task_form.html'
    form_class = TaskForm
    success_url = reverse_lazy('task_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        active_workspace = get_active_workspace(self.request)
        if active_workspace:
            form.fields['project'].queryset = Project.objects.filter(workspace=active_workspace)
        else:
            form.fields['project'].queryset = Project.objects.none()
        return form

class TaskUpdateView(WorkspaceIsolatedMixin, LoginRequiredMixin, TaskAccessMixin, UpdateView):
    model = Task
    template_name = 'tasks/task_form.html'
    form_class = TaskForm
    success_url = reverse_lazy('task_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        active_workspace = get_active_workspace(self.request)
        if active_workspace:
            form.fields['project'].queryset = Project.objects.filter(workspace=active_workspace)
        else:
            form.fields['project'].queryset = Project.objects.none()
        return form

class ProjectDeleteView(WorkspaceIsolatedMixin, LoginRequiredMixin, ProjectAccessMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('dashboard')

class TaskDeleteView(WorkspaceIsolatedMixin, LoginRequiredMixin, TaskAccessMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task_list')

class MarkAllNotificationsReadView(LoginRequiredMixin, APIView):
    def get(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

# --- Hierarchical User Management ---

class TeamListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'core/team_list.html'
    context_object_name = 'team_members'

    def get_queryset(self):
        user = self.request.user
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            return User.objects.none()
            
        qs = User.objects.filter(workspace_memberships__workspace=active_workspace)
        if user.role == 'director':
            return qs.order_by('role')
        elif user.role == 'project_manager':
            return qs.filter(role__in=['project_manager', 'team_member']).order_by('role')
        return qs.filter(id=user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role == 'director':
            context['removal_requests'] = RemovalRequest.objects.filter(status='pending')
        return context

class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = HierarchicalUserCreationForm
    template_name = 'core/user_form.html'
    success_url = reverse_lazy('team_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        active_workspace = get_active_workspace(self.request)
        if active_workspace:
            role_map = 'team_member'
            if self.object.role == 'director':
                role_map = 'owner'
            elif self.object.role == 'project_manager':
                role_map = 'project_manager'
            WorkspaceMembership.objects.create(
                user=self.object,
                workspace=active_workspace,
                role=role_map
            )
        # Notify the new user
        Notification.objects.create(
            recipient=self.object,
            sender=self.request.user,
            message=f"Welcome to Aurevia! Your account has been created as a {self.object.get_role_display()}.",
            notif_type='team'
        )
        messages.success(self.request, f"User {self.object.username} created successfully.")
        return response

class ExportProjectDataView(LoginRequiredMixin, APIView):
    def get(self, request):
        user = request.user
        active_workspace = get_active_workspace(request)
        if not active_workspace:
            projects = Project.objects.none()
        elif user.role == 'director':
            projects = Project.objects.filter(workspace=active_workspace)
        elif user.role == 'project_manager':
            projects = Project.objects.filter(workspace=active_workspace, manager=user)
        else:
            projects = Project.objects.filter(workspace=active_workspace, members=user)

        # Create a CSV response
        class Echo:
            def write(self, value):
                return value

        def iter_items(projects):
            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer)
            yield writer.writerow(['Project ID', 'Title', 'Manager', 'Status', 'Progress', 'End Date'])
            for p in projects:
                yield writer.writerow([
                    p.id, p.title, p.manager.username if p.manager else 'N/A',
                    p.status, f"{p.progress_percentage}%",
                    p.end_date.strftime('%Y-%m-%d') if p.end_date else 'N/A'
                ])

        response = StreamingHttpResponse(iter_items(projects), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="aurevia_projects_{timezone.now().date()}.csv"'
        return response

class RequestRemovalView(LoginRequiredMixin, APIView):
    def post(self, request, pk):
        active_workspace = get_active_workspace(request)
        if not active_workspace:
            messages.error(request, "No active workspace.")
            return redirect('team_list')

        # Must be a member of the active workspace
        target_user = get_object_or_404(User, pk=pk, workspace_memberships__workspace=active_workspace)
        reason = request.POST.get('reason', 'No reason provided.')
        
        # Managers request removal of Members
        if request.user.role == 'project_manager' and target_user.role == 'team_member':
            # Check if request already exists
            if not RemovalRequest.objects.filter(target_user=target_user, status='pending').exists():
                RemovalRequest.objects.create(
                    target_user=target_user,
                    requester=request.user,
                    reason=reason
                )
                # Notify Directors within the workspace
                directors = User.objects.filter(role='director', workspace_memberships__workspace=active_workspace)
                for d in directors:
                    Notification.objects.create(
                        recipient=d,
                        sender=request.user,
                        message=f"Removal request for {target_user.username} initiated by {request.user.username}.",
                        notif_type='removal'
                    )
                messages.info(request, "Removal request sent to Director for approval.")
        
        # Directors can remove directly
        elif request.user.role == 'director' and target_user != request.user:
            target_user.delete()
            messages.success(request, f"User {target_user.username} removed successfully.")
            
        return redirect('team_list')

class ReviewRemovalView(LoginRequiredMixin, APIView):
    def post(self, request, pk):
        if request.user.role != 'director':
            return redirect('dashboard')

        active_workspace = get_active_workspace(request)
        if not active_workspace:
            return redirect('dashboard')
            
        removal_req = get_object_or_404(
            RemovalRequest,
            pk=pk,
            target_user__workspace_memberships__workspace=active_workspace
        )
        action = request.POST.get('action') # 'approve' or 'reject'
        
        if action == 'approve':
            user_to_remove = removal_req.target_user
            username = user_to_remove.username
            user_to_remove.delete()
            removal_req.status = 'approved'
            removal_req.save()
            messages.success(request, f"Removal approved. {username} has been removed.")
            
            # Notify Requester
            Notification.objects.create(
                recipient=removal_req.requester,
                sender=request.user,
                message=f"Your removal request for {username} was approved.",
                notif_type='team'
            )
        else:
            removal_req.status = 'rejected'
            removal_req.save()
            messages.warning(request, "Removal request rejected.")
            
            # Notify Requester
            Notification.objects.create(
                recipient=removal_req.requester,
                sender=request.user,
                message=f"Your removal request for {removal_req.target_user.username} was rejected.",
                notif_type='team'
            )
            
        return redirect('team_list')

class SwitchWorkspaceView(LoginRequiredMixin, APIView):
    def get(self, request, workspace_id):
        from django.core.exceptions import PermissionDenied
        membership = WorkspaceMembership.objects.filter(user=request.user, workspace_id=workspace_id).exists()
        if membership:
            request.session['active_workspace_id'] = workspace_id
            
        next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/'
        if not next_url.startswith('/') and not next_url.startswith(request.build_absolute_uri('/')[:-1]):
            next_url = '/'
        return redirect(next_url)

class WorkspaceSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'core/workspace_settings.html'

    def get_context_data(self, **kwargs):
        from django.http import Http404
        from django.core.exceptions import PermissionDenied
        context = super().get_context_data(**kwargs)
        
        active_workspace = get_active_workspace(self.request)
        if not active_workspace:
            raise Http404("No active workspace found.")

        current_membership = get_object_or_404(WorkspaceMembership, user=self.request.user, workspace=active_workspace)
        if current_membership.role not in ['owner', 'admin']:
            raise PermissionDenied("You do not have permission to view workspace settings.")

        context['workspace'] = active_workspace
        context['memberships'] = WorkspaceMembership.objects.filter(workspace=active_workspace).select_related('user')
        
        existing_members = context['memberships'].values_list('user_id', flat=True)
        context['non_members'] = User.objects.exclude(id__in=existing_members)
        
        return context

    def post(self, request, *args, **kwargs):
        from django.core.exceptions import PermissionDenied
        active_workspace = get_active_workspace(request)
        if not active_workspace:
            return redirect('dashboard')

        current_membership = get_object_or_404(WorkspaceMembership, user=request.user, workspace=active_workspace)
        if current_membership.role not in ['owner', 'admin']:
            raise PermissionDenied("Unauthorized operation.")

        action = request.POST.get('action')
        
        if action == 'invite':
            user_id = request.POST.get('user_id')
            role = request.POST.get('role', 'team_member')
            user_to_add = get_object_or_404(User, id=user_id)
            WorkspaceMembership.objects.get_or_create(
                user=user_to_add,
                workspace=active_workspace,
                defaults={'role': role}
            )
            ActivityLog.objects.create(
                user=request.user,
                workspace=active_workspace,
                action=f"Added member '{user_to_add.username}' as {role}."
            )
            messages.success(request, f"Added {user_to_add.username} to workspace.")
            
        elif action == 'remove':
            membership_id = request.POST.get('membership_id')
            membership_to_remove = get_object_or_404(WorkspaceMembership, id=membership_id, workspace=active_workspace)
            if membership_to_remove.role == 'owner' and current_membership.role != 'owner':
                raise PermissionDenied("Only owners can modify other owners.")
            if membership_to_remove.user == request.user:
                raise PermissionDenied("You cannot remove yourself.")
                
            username = membership_to_remove.user.username
            membership_to_remove.delete()
            ActivityLog.objects.create(
                user=request.user,
                workspace=active_workspace,
                action=f"Removed '{username}' from workspace."
            )
            messages.warning(request, f"Removed {username} from workspace.")
            
        elif action == 'change_role':
            membership_id = request.POST.get('membership_id')
            new_role = request.POST.get('role')
            membership_to_edit = get_object_or_404(WorkspaceMembership, id=membership_id, workspace=active_workspace)
            if membership_to_edit.role == 'owner' and current_membership.role != 'owner':
                raise PermissionDenied("Only the Owner can modify ownership role.")
            
            membership_to_edit.role = new_role
            membership_to_edit.save()
            messages.info(request, f"Updated role of {membership_to_edit.user.username} to {new_role}.")
            
        return redirect('workspace_settings')


class WorkspaceCreateView(LoginRequiredMixin, CreateView):
    model = Workspace
    form_class = WorkspaceForm
    template_name = 'core/workspace_form.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        from django.utils.text import slugify
        
        org, _ = Organization.objects.get_or_create(name="Default Organization")
        
        workspace = form.save(commit=False)
        workspace.organization = org
        workspace.owner = self.request.user
        
        base_slug = slugify(workspace.name)
        if not base_slug:
            base_slug = "workspace"
        slug = base_slug
        counter = 1
        while Workspace.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        workspace.slug = slug
        workspace.save()
        
        WorkspaceMembership.objects.create(
            user=self.request.user,
            workspace=workspace,
            role='owner'
        )
        
        self.request.session['active_workspace_id'] = workspace.id
        
        messages.success(self.request, f"Workspace '{workspace.name}' created successfully, and you have been switched to it.")
        return redirect('dashboard')


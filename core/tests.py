from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from core.models import User
from projects.models import Project
from tasks.models import Task

class NexusFlowSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create Users
        self.director = User.objects.create_user(
            username='director_user', password='password123', role='director'
        )
        self.pm_1 = User.objects.create_user(
            username='pm1_user', password='password123', role='project_manager'
        )
        self.pm_2 = User.objects.create_user(
            username='pm2_user', password='password123', role='project_manager'
        )
        self.member_1 = User.objects.create_user(
            username='member1_user', password='password123', role='team_member'
        )
        self.member_2 = User.objects.create_user(
            username='member2_user', password='password123', role='team_member'
        )

        # Create Organization, Workspace, and Memberships
        from core.models import Organization, Workspace, WorkspaceMembership
        self.org = Organization.objects.create(name='Security Test Org')
        self.workspace = Workspace.objects.create(name='Security Test Workspace', organization=self.org)

        WorkspaceMembership.objects.create(user=self.director, workspace=self.workspace, role='owner')
        WorkspaceMembership.objects.create(user=self.pm_1, workspace=self.workspace, role='project_manager')
        WorkspaceMembership.objects.create(user=self.pm_2, workspace=self.workspace, role='project_manager')
        WorkspaceMembership.objects.create(user=self.member_1, workspace=self.workspace, role='team_member')
        WorkspaceMembership.objects.create(user=self.member_2, workspace=self.workspace, role='team_member')

        # Create Projects
        self.project_1 = Project.objects.create(
            title='Project 1',
            workspace=self.workspace,
            manager=self.pm_1,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=10),
            status='active'
        )
        self.project_1.members.add(self.member_1)

        self.project_2 = Project.objects.create(
            title='Project 2',
            workspace=self.workspace,
            manager=self.pm_2,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=10),
            status='active'
        )
        self.project_2.members.add(self.member_2)

        # Create Tasks
        self.task_1 = Task.objects.create(
            project=self.project_1,
            title='Task 1',
            assignee=self.member_1,
            status='todo',
            priority='medium'
        )
        self.task_2 = Task.objects.create(
            project=self.project_1,
            title='Task 2',
            assignee=self.member_2,
            status='todo',
            priority='medium'
        )

    # --- Project Authorization Tests ---

    def test_project_edit_authorization(self):
        # 1. Director can edit Project 1 (GET form)
        self.client.login(username='director_user', password='password123')
        response = self.client.get(reverse('project_edit', kwargs={'pk': self.project_1.pk}))
        self.assertEqual(response.status_code, 200)

        # 2. PM 1 can edit Project 1
        self.client.login(username='pm1_user', password='password123')
        response = self.client.get(reverse('project_edit', kwargs={'pk': self.project_1.pk}))
        self.assertEqual(response.status_code, 200)

        # 3. PM 2 cannot edit Project 1
        self.client.login(username='pm2_user', password='password123')
        response = self.client.get(reverse('project_edit', kwargs={'pk': self.project_1.pk}))
        self.assertEqual(response.status_code, 403)

        # 4. Team Member 1 cannot edit Project 1
        self.client.login(username='member1_user', password='password123')
        response = self.client.get(reverse('project_edit', kwargs={'pk': self.project_1.pk}))
        self.assertEqual(response.status_code, 403)

    def test_project_delete_authorization(self):
        # 1. Director can delete Project 1
        self.client.login(username='director_user', password='password123')
        response = self.client.get(reverse('project_delete', kwargs={'pk': self.project_1.pk}))
        self.assertEqual(response.status_code, 200)

        # 2. PM 1 can delete Project 1
        self.client.login(username='pm1_user', password='password123')
        response = self.client.get(reverse('project_delete', kwargs={'pk': self.project_1.pk}))
        self.assertEqual(response.status_code, 200)

        # 3. PM 2 cannot delete Project 1
        self.client.login(username='pm2_user', password='password123')
        response = self.client.get(reverse('project_delete', kwargs={'pk': self.project_1.pk}))
        self.assertEqual(response.status_code, 403)

        # 4. Team Member 1 cannot delete Project 1
        self.client.login(username='member1_user', password='password123')
        response = self.client.get(reverse('project_delete', kwargs={'pk': self.project_1.pk}))
        self.assertEqual(response.status_code, 403)

    # --- Task Authorization Tests ---

    def test_task_edit_authorization(self):
        # 1. Director can edit Task 1
        self.client.login(username='director_user', password='password123')
        response = self.client.get(reverse('task_edit', kwargs={'pk': self.task_1.pk}))
        self.assertEqual(response.status_code, 200)

        # 2. PM 1 can edit Task 1 (since they manage the project)
        self.client.login(username='pm1_user', password='password123')
        response = self.client.get(reverse('task_edit', kwargs={'pk': self.task_1.pk}))
        self.assertEqual(response.status_code, 200)

        # 3. PM 2 cannot edit Task 1 (different project manager)
        self.client.login(username='pm2_user', password='password123')
        response = self.client.get(reverse('task_edit', kwargs={'pk': self.task_1.pk}))
        self.assertEqual(response.status_code, 403)

        # 4. Team Member 1 (Assignee) can edit Task 1
        self.client.login(username='member1_user', password='password123')
        response = self.client.get(reverse('task_edit', kwargs={'pk': self.task_1.pk}))
        self.assertEqual(response.status_code, 200)

        # 5. Team Member 2 (Non-Assignee) cannot edit Task 1
        self.client.login(username='member2_user', password='password123')
        response = self.client.get(reverse('task_edit', kwargs={'pk': self.task_1.pk}))
        self.assertEqual(response.status_code, 403)

    def test_task_delete_authorization(self):
        # 1. Director can delete Task 1
        self.client.login(username='director_user', password='password123')
        response = self.client.get(reverse('task_delete', kwargs={'pk': self.task_1.pk}))
        self.assertEqual(response.status_code, 200)

        # 2. PM 1 can delete Task 1
        self.client.login(username='pm1_user', password='password123')
        response = self.client.get(reverse('task_delete', kwargs={'pk': self.task_1.pk}))
        self.assertEqual(response.status_code, 200)

        # 3. PM 2 cannot delete Task 1
        self.client.login(username='pm2_user', password='password123')
        response = self.client.get(reverse('task_delete', kwargs={'pk': self.task_1.pk}))
        self.assertEqual(response.status_code, 403)

        # 4. Team Member 1 (Assignee) can delete Task 1
        self.client.login(username='member1_user', password='password123')
        response = self.client.get(reverse('task_delete', kwargs={'pk': self.task_1.pk}))
        self.assertEqual(response.status_code, 200)

        # 5. Team Member 2 cannot delete Task 1
        self.client.login(username='member2_user', password='password123')
        response = self.client.get(reverse('task_delete', kwargs={'pk': self.task_1.pk}))
        self.assertEqual(response.status_code, 403)

    # --- Project Progress Tests ---

    def test_project_progress_percentage(self):
        # 1. Empty active/planning project with no tasks (0%)
        empty_project = Project.objects.create(title='Empty Project', workspace=self.workspace, manager=self.pm_1, status='active')
        self.assertEqual(empty_project.progress_percentage, 0)
        
        empty_planning = Project.objects.create(title='Empty Planning Project', workspace=self.workspace, manager=self.pm_1, status='planning')
        self.assertEqual(empty_planning.progress_percentage, 0)

        # 2. Completed project with no tasks (should still be 100%)
        completed_project_empty = Project.objects.create(title='Completed Empty Project', workspace=self.workspace, manager=self.pm_1, status='completed')
        self.assertEqual(completed_project_empty.progress_percentage, 100)

        # 3. Project 1 starts with 2 tasks, neither completed (0%)
        self.assertEqual(self.project_1.progress_percentage, 0)

        # 4. Mark 1 task as done (50% completed tasks = 50%)
        self.task_1.status = 'done'
        self.task_1.save()
        self.assertEqual(self.project_1.progress_percentage, 50)

        # 5. Mark second task as done (all tasks completed = 100%)
        self.task_2.status = 'done'
        self.task_2.save()
        self.assertEqual(self.project_1.progress_percentage, 100)

    # --- Dashboard Filtering Tests ---

    def test_dashboard_filtering(self):
        # Create a completed project to test filtering
        project_completed = Project.objects.create(
            title='Project Completed',
            workspace=self.workspace,
            manager=self.pm_1,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=10),
            status='completed'
        )

        self.client.login(username='director_user', password='password123')
        
        # 1. No filter (All) -> should return all 3 projects
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['projects']), 3)

        # 2. Filter active -> should return 2 active projects
        response = self.client.get(reverse('dashboard') + '?status=active')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['projects']), 2)
        for p in response.context['projects']:
            self.assertEqual(p.status, 'active')

        # 3. Filter completed -> should return 1 completed project
        response = self.client.get(reverse('dashboard') + '?status=completed')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['projects']), 1)
        self.assertEqual(response.context['projects'][0].status, 'completed')

        # 4. Filter planning -> should return 0 planning projects
        response = self.client.get(reverse('dashboard') + '?status=planning')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['projects']), 0)


class NexusFlowRiskEngineTests(TestCase):
    def setUp(self):
        # Create Users
        self.pm = User.objects.create_user(username='risk_pm', password='password123', role='project_manager')
        self.member_1 = User.objects.create_user(username='risk_member1', password='password123', role='team_member')
        self.member_2 = User.objects.create_user(username='risk_member2', password='password123', role='team_member')

        # Baseline dates
        self.today = timezone.now().date()
        self.start_date = self.today
        self.end_date = self.today + timezone.timedelta(days=10)

    def test_planning_project_skipped(self):
        from core.services.risk_engine import RiskEngine
        project = Project.objects.create(
            title='Planning Project', manager=self.pm, status='planning',
            start_date=self.start_date, end_date=self.end_date
        )
        engine = RiskEngine()
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.status, 'not_started')
        self.assertEqual(analysis.score, 0)
        self.assertEqual(len(analysis.risks), 0)

    def test_completed_project_skipped(self):
        from core.services.risk_engine import RiskEngine
        project = Project.objects.create(
            title='Completed Project', manager=self.pm, status='completed',
            start_date=self.start_date, end_date=self.end_date
        )
        engine = RiskEngine()
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.status, 'completed')
        self.assertEqual(analysis.score, 0)
        self.assertEqual(len(analysis.risks), 0)

    def test_zero_task_active_project(self):
        from core.services.risk_engine import RiskEngine
        project = Project.objects.create(
            title='Zero Tasks Project', manager=self.pm, status='active',
            start_date=self.start_date, end_date=self.end_date
        )
        engine = RiskEngine()
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.score, 10)  # Rule Z triggers: +10
        self.assertEqual(analysis.status, 'on_track')
        self.assertTrue(any(r.rule_code == 'rule_z' for r in analysis.risks))

    def test_zero_task_overdue_project(self):
        from core.services.risk_engine import RiskEngine
        # end date is in the past
        past_end_date = self.today - timezone.timedelta(days=2)
        project = Project.objects.create(
            title='Overdue Zero Tasks Project', manager=self.pm, status='active',
            start_date=self.start_date, end_date=past_end_date
        )
        engine = RiskEngine()
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.score, 40)  # Rule Z (+10) + Rule F (+30) = 40
        self.assertEqual(analysis.status, 'at_risk')

    def test_overdue_project_deadline(self):
        from core.services.risk_engine import RiskEngine
        past_end_date = self.today - timezone.timedelta(days=1)
        project = Project.objects.create(
            title='Overdue Project', manager=self.pm, status='active',
            start_date=self.start_date, end_date=past_end_date
        )
        # Add a task to satisfy Rule Z (making sure it doesn't trigger)
        Task.objects.create(project=project, title='T1', assignee=self.member_1, status='todo')
        
        engine = RiskEngine()
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.score, 30)  # Rule F triggers: +30
        self.assertEqual(analysis.status, 'at_risk')

    def test_task_deadline_conflict(self):
        from core.services.risk_engine import RiskEngine
        project = Project.objects.create(
            title='Conflict Project', manager=self.pm, status='active',
            start_date=self.start_date, end_date=self.end_date
        )
        # Add task with due date past project end date
        conflicting_due_date = self.end_date + timezone.timedelta(days=2)
        Task.objects.create(project=project, title='Conflicting Task', due_date=conflicting_due_date, status='todo')
        
        engine = RiskEngine()
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.score, 20)  # Rule B triggers: +20
        self.assertEqual(analysis.status, 'on_track')

    def test_overdue_task(self):
        from core.services.risk_engine import RiskEngine
        project = Project.objects.create(
            title='Overdue Task Project', manager=self.pm, status='active',
            start_date=self.start_date, end_date=self.end_date
        )
        # Add task with due date past today (yesterday)
        yesterday = self.today - timezone.timedelta(days=1)
        Task.objects.create(project=project, title='Overdue Task', due_date=yesterday, status='todo')
        
        engine = RiskEngine()
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.score, 15)  # Rule A triggers: +15
        self.assertEqual(analysis.status, 'on_track')

    def test_completed_overdue_task_skipped(self):
        from core.services.risk_engine import RiskEngine
        project = Project.objects.create(
            title='Completed Task Project', manager=self.pm, status='active',
            start_date=self.start_date, end_date=self.end_date
        )
        yesterday = self.today - timezone.timedelta(days=1)
        # Completed task (done) with past due date
        Task.objects.create(project=project, title='Completed Overdue Task', due_date=yesterday, status='done')
        
        engine = RiskEngine()
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.score, 0)  # Should skip completed tasks
        self.assertEqual(analysis.status, 'on_track')

    def test_dependency_blocker(self):
        from core.services.risk_engine import RiskEngine
        project = Project.objects.create(
            title='Dependency Project', manager=self.pm, status='active',
            start_date=self.start_date, end_date=self.end_date
        )
        t_blocker = Task.objects.create(project=project, title='Blocker Task', status='todo')
        t_blocked = Task.objects.create(project=project, title='Blocked Task', status='todo')
        t_blocked.dependencies.add(t_blocker)
        
        engine = RiskEngine()
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.score, 10)  # Rule C triggers: +10
        self.assertEqual(analysis.status, 'on_track')

    def test_resource_overload(self):
        from core.services.risk_engine import RiskEngine
        # Create 4 active tasks assigned to member_1 across multiple projects
        project_a = Project.objects.create(title='Project A', manager=self.pm, status='active')
        project_b = Project.objects.create(title='Project B', manager=self.pm, status='active')
        
        Task.objects.create(project=project_a, title='T1', assignee=self.member_1, status='todo')
        Task.objects.create(project=project_a, title='T2', assignee=self.member_1, status='todo')
        Task.objects.create(project=project_b, title='T3', assignee=self.member_1, status='todo')
        Task.objects.create(project=project_b, title='T4', assignee=self.member_1, status='todo')
        
        engine = RiskEngine()
        analysis_a = engine.analyze_project(project_a, today=self.today)
        # Triggers Resource Overload for member_1 (+10)
        self.assertEqual(analysis_a.score, 10)

    def test_timeline_lag(self):
        from core.services.risk_engine import RiskEngine
        # 80% elapsed (start 8 days ago, end 2 days from now)
        start = self.today - timezone.timedelta(days=8)
        end = self.today + timezone.timedelta(days=2)
        project = Project.objects.create(
            title='Lag Project', manager=self.pm, status='active',
            start_date=start, end_date=end
        )
        # Create 2 active tasks (progress = 0%)
        # Timeline elapsed is 80%. Lag is 80% - 0% = 80% (> 25%)
        Task.objects.create(project=project, title='T1', status='todo')
        Task.objects.create(project=project, title='T2', status='todo')
        
        engine = RiskEngine()
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.score, 25)  # Rule E triggers: +25
        self.assertEqual(analysis.status, 'on_track')

    def test_missing_dates_handling(self):
        from core.services.risk_engine import RiskEngine
        project = Project.objects.create(
            title='No Dates Project', manager=self.pm, status='active'
        )
        Task.objects.create(project=project, title='T1', status='todo')
        engine = RiskEngine()
        # Should not crash on missing dates
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.score, 0)

    def test_equal_start_end_dates(self):
        from core.services.risk_engine import RiskEngine
        project = Project.objects.create(
            title='Same Dates Project', manager=self.pm, status='active',
            start_date=self.today, end_date=self.today
        )
        Task.objects.create(project=project, title='T1', status='todo')
        engine = RiskEngine()
        # Should not divide by zero
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.score, 25)  # Today >= end_date (elapsed ratio forced to 1.0, lag = 100% - 0% = 100% > 25)

    def test_future_start_date(self):
        from core.services.risk_engine import RiskEngine
        future_start = self.today + timezone.timedelta(days=2)
        future_end = self.today + timezone.timedelta(days=10)
        project = Project.objects.create(
            title='Future Project', manager=self.pm, status='active',
            start_date=future_start, end_date=future_end
        )
        Task.objects.create(project=project, title='T1', status='todo')
        engine = RiskEngine()
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.score, 0)  # Elapsed ratio should be 0.0, no lag triggers

    def test_circular_dependencies(self):
        from core.services.risk_engine import RiskEngine
        project = Project.objects.create(title='Cycle Project', manager=self.pm, status='active')
        t1 = Task.objects.create(project=project, title='T1', status='todo')
        t2 = Task.objects.create(project=project, title='T2', status='todo')
        t1.dependencies.add(t2)
        t2.dependencies.add(t1)  # Cycle created
        
        engine = RiskEngine()
        # Ensure evaluate handles circular dependencies safely (no recursion limit crash)
        analysis = engine.analyze_project(project, today=self.today)
        self.assertEqual(analysis.score, 20)  # Both blocked: 2 * 10 = 20

    def test_maximum_score_capped(self):
        from core.services.risk_engine import RiskEngine
        # Cumulate many risks to exceed 100 points
        past_end_date = self.today - timezone.timedelta(days=2)
        project = Project.objects.create(
            title='Heavy Risk Project', manager=self.pm, status='active',
            start_date=self.start_date, end_date=past_end_date
        )
        # Overdue tasks (+15 each, cap 45)
        yesterday = self.today - timezone.timedelta(days=1)
        for i in range(4):
            t = Task.objects.create(project=project, title=f'Overdue T{i}', due_date=yesterday, status='todo')
            
        # Deadline conflicts (+20 each, cap 40)
        conflicting_due_date = past_end_date + timezone.timedelta(days=10)
        for i in range(3):
            Task.objects.create(project=project, title=f'Conflict T{i}', due_date=conflicting_due_date, status='todo')

        engine = RiskEngine()
        analysis = engine.analyze_project(project, today=self.today)
        # Accumulated points exceed 100 (45 + 40 + 30 = 115) but must be capped at 100
        self.assertEqual(analysis.score, 100)
        self.assertEqual(analysis.status, 'off_track')

    def test_assert_num_queries(self):
        from core.services.risk_engine import RiskEngine
        # Create 5 active projects with multiple tasks to evaluate database efficiency
        projects_list = []
        for i in range(5):
            p = Project.objects.create(title=f'Bulk Project {i}', manager=self.pm, status='active')
            t1 = Task.objects.create(project=p, title=f'Task {i}.1', assignee=self.member_1, status='todo')
            t2 = Task.objects.create(project=p, title=f'Task {i}.2', assignee=self.member_2, status='todo')
            t2.dependencies.add(t1)
            projects_list.append(p)

        # Refresh database queries using prefetches
        db_projects = list(Project.objects.all().select_related('manager').prefetch_related(
            'tasks',
            'tasks__assignee',
            'tasks__dependencies'
        ))

        engine = RiskEngine()
        # Assert query footprint is constant (O(1)) during multi-project scan:
        # 1 query for getting active counts (overloaded users check)
        # Any other operations should run entirely in-memory because of prefetching.
        with self.assertNumQueries(1):
            analyses = engine.analyze_multiple_projects(db_projects, today=self.today)
            self.assertEqual(len(analyses), len(db_projects))


class NexusFlowWorkspaceTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from core.models import Organization, Workspace, WorkspaceMembership
        User = get_user_model()
        
        self.user_a = User.objects.create_user(username='usera', password='password123', email='usera@test.com', role='director')
        self.user_b = User.objects.create_user(username='userb', password='password123', email='userb@test.com', role='team_member')
        
        self.org = Organization.objects.create(name='Test Org')
        self.workspace_a = Workspace.objects.create(name='Workspace A', organization=self.org)
        self.workspace_b = Workspace.objects.create(name='Workspace B', organization=self.org)
        
        WorkspaceMembership.objects.create(user=self.user_a, workspace=self.workspace_a, role='owner')
        WorkspaceMembership.objects.create(user=self.user_b, workspace=self.workspace_b, role='team_member')
        
        self.project_a = Project.objects.create(title='Project Alpha', workspace=self.workspace_a, manager=self.user_a)
        self.project_b = Project.objects.create(title='Project Beta', workspace=self.workspace_b, manager=self.user_a)

    def test_workspace_membership_and_switching(self):
        self.client.login(username='usera', password='password123')
        
        # Test default active workspace context
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('active_workspace', response.context)
        self.assertEqual(response.context['active_workspace'].id, self.workspace_a.id)
        
        # Add user_a to workspace_b
        from core.models import WorkspaceMembership
        WorkspaceMembership.objects.create(user=self.user_a, workspace=self.workspace_b, role='admin')
        
        # Test workspace switching view
        response = self.client.get(f'/workspaces/switch/{self.workspace_b.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['active_workspace_id']), self.workspace_b.id)

    def test_project_isolation(self):
        # User A in Workspace A
        self.client.login(username='usera', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.workspace_a.id
        session.save()
        
        response = self.client.get('/')
        self.assertContains(response, 'Project Alpha')
        self.assertNotContains(response, 'Project Beta')

    def test_workspace_settings_permissions(self):
        # User B is team_member, shouldn't have access to settings
        self.client.login(username='userb', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.workspace_b.id
        session.save()
        
        response = self.client.get('/workspace/settings/')
        self.assertEqual(response.status_code, 403)

        # User A is owner, should have access to settings
        self.client.login(username='usera', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.workspace_a.id
        session.save()
        
        response = self.client.get('/workspace/settings/')
        self.assertEqual(response.status_code, 200)

    def test_workspace_creation(self):
        self.client.login(username='usera', password='password123')
        response = self.client.post('/workspace/create/', {'name': 'New Dev Workspace'})
        self.assertEqual(response.status_code, 302)
        
        from core.models import Workspace, WorkspaceMembership
        new_ws = Workspace.objects.get(name='New Dev Workspace')
        self.assertEqual(new_ws.owner, self.user_a)
        self.assertTrue(new_ws.slug)
        self.assertEqual(int(self.client.session['active_workspace_id']), new_ws.id)
        
        membership = WorkspaceMembership.objects.get(user=self.user_a, workspace=new_ws)
        self.assertEqual(membership.role, 'owner')

    def test_duplicate_membership_prevention(self):
        from core.models import WorkspaceMembership
        with self.assertRaises(Exception):
            WorkspaceMembership.objects.create(user=self.user_a, workspace=self.workspace_a, role='team_member')

    def test_workspace_dashboard_counts_and_team(self):
        Project.objects.create(title='Alpha Project 2', workspace=self.workspace_a, manager=self.user_a)
        
        # Add user_a to workspace_b so they have access to switch
        from core.models import WorkspaceMembership
        WorkspaceMembership.objects.create(user=self.user_a, workspace=self.workspace_b, role='admin')
        
        self.client.login(username='usera', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.workspace_a.id
        session.save()
        
        response = self.client.get('/')
        self.assertEqual(response.context['total_projects'], 2)
        
        session['active_workspace_id'] = self.workspace_b.id
        session.save()
        
        response = self.client.get('/')
        self.assertEqual(response.context['total_projects'], 1)

    def test_workspace_settings_member_flow(self):
        self.client.login(username='usera', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.workspace_a.id
        session.save()
        
        # Invite User B
        response = self.client.post('/workspace/settings/', {
            'action': 'invite',
            'user_id': self.user_b.id,
            'role': 'team_member'
        })
        self.assertEqual(response.status_code, 302)
        
        from core.models import WorkspaceMembership
        self.assertTrue(WorkspaceMembership.objects.filter(user=self.user_b, workspace=self.workspace_a, role='team_member').exists())
        
        # Change Role
        membership = WorkspaceMembership.objects.get(user=self.user_b, workspace=self.workspace_a)
        response = self.client.post('/workspace/settings/', {
            'action': 'change_role',
            'membership_id': membership.id,
            'role': 'project_manager'
        })
        self.assertEqual(response.status_code, 302)
        membership.refresh_from_db()
        self.assertEqual(membership.role, 'project_manager')
        
        # Remove
        response = self.client.post('/workspace/settings/', {
            'action': 'remove',
            'membership_id': membership.id
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(WorkspaceMembership.objects.filter(user=self.user_b, workspace=self.workspace_a).exists())


class AureviaTenantSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()

        from core.models import Organization, Workspace, WorkspaceMembership
        # Synthetic Tenant A
        self.org_a = Organization.objects.create(name='Tenant A Org')
        self.ws_a = Workspace.objects.create(name='Tenant A Workspace', organization=self.org_a)
        self.director_a = User.objects.create_user(username='director_a', password='password123', role='director')
        WorkspaceMembership.objects.create(user=self.director_a, workspace=self.ws_a, role='owner')

        self.project_a = Project.objects.create(
            title='Project Alpha',
            workspace=self.ws_a,
            manager=self.director_a,
            status='active',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=10)
        )
        self.task_a = Task.objects.create(
            project=self.project_a,
            title='Task Alpha',
            assignee=self.director_a,
            status='todo',
            priority='medium'
        )

        # Synthetic Tenant B (Secret)
        self.org_b = Organization.objects.create(name='Tenant B Org')
        self.ws_b = Workspace.objects.create(name='Tenant B Workspace', organization=self.org_b)
        self.director_b = User.objects.create_user(username='director_b', password='password123', role='director')
        WorkspaceMembership.objects.create(user=self.director_b, workspace=self.ws_b, role='owner')

        self.project_b = Project.objects.create(
            title='Project Beta (Confidential)',
            workspace=self.ws_b,
            manager=self.director_b,
            status='active',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=10)
        )
        self.task_b = Task.objects.create(
            project=self.project_b,
            title='Task Beta (Confidential)',
            assignee=self.director_b,
            status='todo',
            priority='high'
        )

    def test_director_cannot_view_cross_tenant_projects_or_tasks_in_dashboard_api(self):
        """
        Verify that a user with the global role of 'director' in Tenant A cannot
        retrieve Tenant B's projects or tasks through the Dashboard API.
        """
        self.client.login(username='director_a', password='password123')

        # 1. Standard request with active workspace in session
        session = self.client.session
        session['active_workspace_id'] = self.ws_a.id
        session.save()

        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_projects'], 1)
        self.assertEqual(response.data['total_tasks'], 1)

        # 2. Malicious probe: Tenant A director attempts to query Tenant B's workspace
        response_probe = self.client.get(f'/api/dashboard/?workspace_id={self.ws_b.id}')
        self.assertEqual(response_probe.status_code, 200)
        # Should return 0 results because director_a is not a member of ws_b
        self.assertEqual(response_probe.data['total_projects'], 0)
        self.assertEqual(response_probe.data['total_tasks'], 0)

    def test_get_request_without_active_workspace_does_not_mutate_db_or_reassign_projects(self):
        """
        Verify that an authenticated user who has no active workspace cannot trigger
        automatic workspace creation, membership creation, or unassigned project reassignment
        merely by issuing GET requests to web or API endpoints.
        """
        from core.models import Organization, Workspace, WorkspaceMembership

        # Create user without any workspace memberships
        unassigned_user = User.objects.create_user(
            username='unassigned_user',
            password='password123',
            role='director'
        )
        unassigned_project = Project.objects.create(
            title='Unassigned Sensitive Project',
            workspace=None,
            manager=unassigned_user,
            status='active'
        )

        initial_org_count = Organization.objects.count()
        initial_ws_count = Workspace.objects.count()
        initial_membership_count = WorkspaceMembership.objects.count()

        self.client.login(username='unassigned_user', password='password123')

        # Issue GET request to web dashboard
        response_web = self.client.get('/')
        self.assertEqual(response_web.status_code, 200)

        # Issue GET request to API dashboard
        response_api = self.client.get('/api/dashboard/')
        self.assertEqual(response_api.status_code, 200)
        self.assertEqual(response_api.data['total_projects'], 0)

        # Assert no database records were created
        self.assertEqual(Organization.objects.count(), initial_org_count)
        self.assertEqual(Workspace.objects.count(), initial_ws_count)
        self.assertEqual(WorkspaceMembership.objects.count(), initial_membership_count)

        # Assert unassigned project was NOT mutated or reassigned
        unassigned_project.refresh_from_db()
        self.assertIsNone(unassigned_project.workspace)

    def test_cross_tenant_isolation_in_project_and_task_api_viewsets(self):
        """
        Verify that Tenant A director cannot retrieve Tenant B's projects or tasks
        via list or detail API endpoints.
        """
        self.client.login(username='director_a', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.ws_a.id
        session.save()

        # 1. Project list API
        response_projects = self.client.get('/api/projects/')
        self.assertEqual(response_projects.status_code, 200)
        # Should only contain Tenant A project
        project_ids = [p['id'] for p in response_projects.data]
        self.assertIn(self.project_a.id, project_ids)
        self.assertNotIn(self.project_b.id, project_ids)

        # 2. Task list API
        response_tasks = self.client.get('/api/tasks/')
        self.assertEqual(response_tasks.status_code, 200)
        task_ids = [t['id'] for t in response_tasks.data]
        self.assertIn(self.task_a.id, task_ids)
        self.assertNotIn(self.task_b.id, task_ids)

        # 3. Direct detail access to Tenant B project should be forbidden or not found
        response_proj_detail = self.client.get(f'/api/projects/{self.project_b.id}/')
        self.assertIn(response_proj_detail.status_code, [403, 404])

        # 4. Direct detail access to Tenant B task should be forbidden or not found
        response_task_detail = self.client.get(f'/api/tasks/{self.task_b.id}/')
        self.assertIn(response_task_detail.status_code, [403, 404])

    def test_export_project_data_isolated_to_active_workspace(self):
        """Verify that CSV export contains only projects from active workspace."""
        self.client.login(username='director_a', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.ws_a.id
        session.save()

        response = self.client.get('/export/projects/')
        self.assertEqual(response.status_code, 200)
        content = b"".join(response.streaming_content).decode('utf-8')
        self.assertIn('Project Alpha', content)
        self.assertNotIn('Project Beta', content)

    def test_document_viewset_isolation_and_permissions(self):
        """Verify cross-workspace document listing, retrieval, deletion and creation are rejected."""
        from documents.models import Document
        from django.core.files.uploadedfile import SimpleUploadedFile

        doc_a = Document.objects.create(
            title='Doc A',
            project=self.project_a,
            uploaded_by=self.director_a,
            file=SimpleUploadedFile('test_a.txt', b'tenant a content')
        )
        doc_b = Document.objects.create(
            title='Doc B (Confidential)',
            project=self.project_b,
            uploaded_by=self.director_b,
            file=SimpleUploadedFile('test_b.txt', b'tenant b content')
        )

        self.client.login(username='director_a', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.ws_a.id
        session.save()

        # 1. List only sees doc_a
        resp_list = self.client.get('/api/documents/')
        self.assertEqual(resp_list.status_code, 200)
        doc_ids = [d['id'] for d in resp_list.data]
        self.assertIn(doc_a.id, doc_ids)
        self.assertNotIn(doc_b.id, doc_ids)

        # 2. Detail access to doc_b rejected
        resp_detail = self.client.get(f'/api/documents/{doc_b.id}/')
        self.assertIn(resp_detail.status_code, [403, 404])

        # 3. Cannot attach document to Tenant B project
        resp_create = self.client.post('/api/documents/', {
            'title': 'Intruder Doc',
            'project': self.project_b.id,
            'file': SimpleUploadedFile('intruder.txt', b'evil')
        })
        self.assertIn(resp_create.status_code, [400, 403])

    def test_activity_log_viewset_isolation(self):
        """Verify activity log API never exposes events from another workspace."""
        from history.models import ActivityLog
        log_a = ActivityLog.objects.create(user=self.director_a, workspace=self.ws_a, action="Tenant A Action")
        log_b = ActivityLog.objects.create(user=self.director_b, workspace=self.ws_b, action="Tenant B Secret Action")

        self.client.login(username='director_a', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.ws_a.id
        session.save()

        resp = self.client.get('/api/history/')
        self.assertEqual(resp.status_code, 200)
        log_actions = [l['action'] for l in resp.data]
        self.assertIn("Tenant A Action", log_actions)
        self.assertNotIn("Tenant B Secret Action", log_actions)

    def test_message_viewset_isolation_and_privacy(self):
        """Verify messages cannot expose foreign workspace messages or private messages between others."""
        from communications.models import Message
        msg_a = Message.objects.create(sender=self.director_a, project=self.project_a, content="Msg A")
        msg_b = Message.objects.create(sender=self.director_b, project=self.project_b, content="Msg B Private")

        self.client.login(username='director_a', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.ws_a.id
        session.save()

        # List
        resp = self.client.get('/api/messages/')
        self.assertEqual(resp.status_code, 200)
        contents = [m['content'] for m in resp.data]
        self.assertIn("Msg A", contents)
        self.assertNotIn("Msg B Private", contents)

        # Cross-workspace creation rejected
        resp_create = self.client.post('/api/messages/', {
            'project': self.project_b.id,
            'content': 'Cross-tenant message'
        })
        self.assertIn(resp_create.status_code, [400, 403])

    def test_child_task_viewsets_rejection_and_mutation_isolation(self):
        """Verify SubTasks, TaskComments, and TimeLogs reject cross-workspace access."""
        from tasks.models import SubTask, TaskComment, TimeLog
        from datetime import timedelta
        sub_a = SubTask.objects.create(task=self.task_a, title='Sub A')
        sub_b = SubTask.objects.create(task=self.task_b, title='Sub B Secret')
        comment_b = TaskComment.objects.create(task=self.task_b, user=self.director_b, content='Comment B')
        log_b = TimeLog.objects.create(
            task=self.task_b,
            user=self.director_b,
            start_time=timezone.now(),
            duration=timedelta(hours=2)
        )

        self.client.login(username='director_a', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.ws_a.id
        session.save()

        # SubTask list
        resp_sub = self.client.get('/api/subtasks/')
        self.assertEqual(resp_sub.status_code, 200)
        sub_ids = [s['id'] for s in resp_sub.data]
        self.assertIn(sub_a.id, sub_ids)
        self.assertNotIn(sub_b.id, sub_ids)

        # SubTask cross-create rejected
        resp_sub_create = self.client.post('/api/subtasks/', {'task': self.task_b.id, 'title': 'Hacked Sub'})
        self.assertIn(resp_sub_create.status_code, [400, 403])

        # TaskComment cross-create rejected
        resp_comment_create = self.client.post('/api/comments/', {'task': self.task_b.id, 'content': 'Hacked Comment'})
        self.assertIn(resp_comment_create.status_code, [400, 403])

        # TimeLog cross-create rejected
        resp_log_create = self.client.post('/api/timelogs/', {'task': self.task_b.id, 'start_time': timezone.now().isoformat()})
        self.assertIn(resp_log_create.status_code, [400, 403])

    def test_cross_workspace_task_creation_rejected(self):
        """Verify user cannot attach a task to a project in another workspace."""
        self.client.login(username='director_a', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.ws_a.id
        session.save()

        resp = self.client.post('/api/tasks/', {
            'project': self.project_b.id,
            'title': 'Foreign Task Injection',
            'status': 'todo',
            'priority': 'high'
        })
        self.assertIn(resp.status_code, [400, 403])
        self.assertFalse(Task.objects.filter(title='Foreign Task Injection').exists())

    def test_project_creation_without_active_workspace_rejected(self):
        """Verify API project creation without active workspace is rejected and creates no record."""
        unassigned_user = User.objects.create_user(username='no_ws_user', password='password123', role='project_manager')
        self.client.login(username='no_ws_user', password='password123')

        resp = self.client.post('/api/projects/', {
            'title': 'Orphan API Project',
            'status': 'planning'
        })
        self.assertIn(resp.status_code, [400, 403])
        self.assertFalse(Project.objects.filter(title='Orphan API Project').exists())

    def test_user_viewset_cannot_enumerate_or_modify_foreign_users(self):
        """Verify user cannot enumerate, retrieve or modify users outside active workspace."""
        self.client.login(username='director_a', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.ws_a.id
        session.save()

        resp = self.client.get('/api/users/')
        self.assertEqual(resp.status_code, 200)
        user_ids = [u['id'] for u in resp.data]
        self.assertIn(self.director_a.id, user_ids)
        self.assertNotIn(self.director_b.id, user_ids)

        resp_detail = self.client.get(f'/api/users/{self.director_b.id}/')
        self.assertIn(resp_detail.status_code, [403, 404])

    def test_request_removal_cannot_delete_foreign_user(self):
        """Verify director cannot delete a user from another workspace via RequestRemovalView."""
        self.client.login(username='director_a', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.ws_a.id
        session.save()

        resp = self.client.post(f'/users/{self.director_b.id}/remove/')
        # Should not delete director_b
        self.assertTrue(User.objects.filter(id=self.director_b.id).exists())

    def test_college_access_policy_is_institutional_executive_requires_workspace_membership(self):
        """Verify is_institutional_executive does not grant access to foreign workspace for director."""
        from academics.services import CollegeAccessPolicy
        # director_a has role='director', but only belongs to ws_a
        self.assertTrue(CollegeAccessPolicy.is_institutional_executive(self.director_a, self.ws_a))
        self.assertFalse(CollegeAccessPolicy.is_institutional_executive(self.director_a, self.ws_b))

    def test_demo_branding_and_export_filename_consistency(self):
        """Verify export projects filename and login persona branding alignment."""
        self.client.login(username='director_a', password='password123')
        session = self.client.session
        session['active_workspace_id'] = self.ws_a.id
        session.save()

        # Export filename must be aurevia_projects_{date}.csv
        response = self.client.get('/export/projects/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('aurevia_projects_', response['Content-Disposition'])

        # Login page persona buttons must feature Aurevia2026!
        self.client.logout()
        resp_login = self.client.get('/login/')
        self.assertEqual(resp_login.status_code, 200)
        self.assertContains(resp_login, 'Aurevia2026!')
        self.assertNotContains(resp_login, 'NexusFlow123!')

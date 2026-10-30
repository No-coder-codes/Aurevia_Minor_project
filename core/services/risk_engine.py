from django.utils import timezone
from django.db.models import Count, Q
from typing import List, Optional

class RiskResult:
    """Represents a single detected risk factor on a project or task."""
    def __init__(self, rule_code: str, severity: str, score_addition: int, description: str, target_id: Optional[int] = None):
        self.rule_code = rule_code        # e.g., 'rule_a', 'rule_b', etc.
        self.severity = severity          # 'low', 'medium', 'high'
        self.score_addition = score_addition
        self.description = description
        self.target_id = target_id        # ID of the affected task/user if applicable

class ProjectRiskAnalysis:
    """Result container for a project's compiled risk intelligence report."""
    def __init__(self, project, score: int, status: str, risks: List[RiskResult], recommendations: List[str]):
        self.project = project
        self.score = score
        self.status = status              # 'on_track', 'at_risk', 'off_track', 'not_started'
        self.risks = risks
        self.recommendations = recommendations

class RiskRule:
    """Base class for all Risk Intelligence Rules."""
    def evaluate(self, project, active_tasks, today, context_data=None) -> List[RiskResult]:
        raise NotImplementedError

class OverdueTaskRule(RiskRule):
    def evaluate(self, project, active_tasks, today, context_data=None) -> List[RiskResult]:
        results = []
        overdue_count = 0
        for task in active_tasks:
            if task.due_date and task.due_date < today:
                overdue_count += 1
                if overdue_count <= 3:  # Only add up to cap
                    results.append(RiskResult(
                        rule_code='rule_a',
                        severity='medium',
                        score_addition=15,
                        description=f"Task '{task.title}' is overdue (due: {task.due_date.strftime('%Y-%m-%d')}).",
                        target_id=task.id
                    ))
        return results

class TaskExceedsDeadlineRule(RiskRule):
    def evaluate(self, project, active_tasks, today, context_data=None) -> List[RiskResult]:
        results = []
        if not project.end_date:
            return results

        conflict_count = 0
        for task in active_tasks:
            if task.due_date and task.due_date > project.end_date:
                conflict_count += 1
                if conflict_count <= 2:  # Only add up to cap
                    results.append(RiskResult(
                        rule_code='rule_b',
                        severity='high',
                        score_addition=20,
                        description=f"Task '{task.title}' due date ({task.due_date.strftime('%Y-%m-%d')}) exceeds the project end date ({project.end_date.strftime('%Y-%m-%d')}).",
                        target_id=task.id
                    ))
        return results

class DependencyBlockerRule(RiskRule):
    def evaluate(self, project, active_tasks, today, context_data=None) -> List[RiskResult]:
        results = []
        blocked_count = 0
        
        # Local circle check helper to prevent infinite loops if circular dependencies exist
        for task in active_tasks:
            # Check if task has any incomplete dependencies
            # We already prefetched 'dependencies' in RiskEngine for performance
            blockers = [dep for dep in task.dependencies.all() if dep.status != 'done']
            if blockers:
                blocked_count += 1
                if blocked_count <= 3:  # Only add up to cap
                    blocker_titles = ", ".join([f"'{b.title}'" for b in blockers[:2]])
                    results.append(RiskResult(
                        rule_code='rule_c',
                        severity='medium',
                        score_addition=10,
                        description=f"Task '{task.title}' is blocked by incomplete task(s): {blocker_titles}.",
                        target_id=task.id
                    ))
        return results

class ResourceOverloadRule(RiskRule):
    def evaluate(self, project, active_tasks, today, context_data=None) -> List[RiskResult]:
        results = []
        if not context_data or 'overloaded_users' not in context_data:
            return results
            
        overloaded_users = context_data['overloaded_users']
        project_assignees_checked = set()
        overloaded_count = 0

        for task in active_tasks:
            if task.assignee and task.assignee.id in overloaded_users:
                user_id = task.assignee.id
                if user_id not in project_assignees_checked:
                    project_assignees_checked.add(user_id)
                    overloaded_count += 1
                    active_count = overloaded_users[user_id]
                    if overloaded_count <= 2:  # Only add up to cap
                        results.append(RiskResult(
                            rule_code='rule_d',
                            severity='medium',
                            score_addition=10,
                            description=f"Team member '{task.assignee.username}' is overloaded with {active_count} active tasks across projects.",
                            target_id=task.assignee.id
                        ))
        return results

class TimelineProgressRule(RiskRule):
    def evaluate(self, project, active_tasks, today, context_data=None) -> List[RiskResult]:
        results = []
        if not project.start_date or not project.end_date:
            return results

        # Skip progress lag check if project has no tasks
        total_tasks_count = context_data.get('total_tasks_count', 0) if context_data else project.tasks.count()
        if total_tasks_count == 0:
            return results

        # Prevent division by zero
        if project.start_date == project.end_date:
            elapsed_ratio = 1.0 if today >= project.end_date else 0.0
        else:
            total_days = (project.end_date - project.start_date).days
            elapsed_days = (today - project.start_date).days
            elapsed_ratio = elapsed_days / total_days
            elapsed_ratio = max(0.0, min(1.0, elapsed_ratio))

        # Check progress lag
        if elapsed_ratio > 0.1:  # Only trigger if timeline has elapsed by > 10%
            elapsed_percentage = int(elapsed_ratio * 100)
            progress = project.progress_percentage
            lag = elapsed_percentage - progress
            if lag > 25:
                results.append(RiskResult(
                    rule_code='rule_e',
                    severity='high',
                    score_addition=25,
                    description=f"Project progress ({progress}%) is lagging {lag}% behind the elapsed schedule ({elapsed_percentage}% elapsed)."
                ))
        return results

class ProjectOverdueRule(RiskRule):
    def evaluate(self, project, active_tasks, today, context_data=None) -> List[RiskResult]:
        results = []
        if project.end_date and today > project.end_date:
            results.append(RiskResult(
                rule_code='rule_f',
                severity='high',
                score_addition=30,
                description=f"Project deadline ({project.end_date.strftime('%Y-%m-%d')}) has already passed, but project remains active."
            ))
        return results

class ZeroTasksRule(RiskRule):
    def evaluate(self, project, active_tasks, today, context_data=None) -> List[RiskResult]:
        results = []
        total_tasks_count = context_data.get('total_tasks_count', 0) if context_data else project.tasks.count()
        if total_tasks_count == 0:
            results.append(RiskResult(
                rule_code='rule_z',
                severity='medium',
                score_addition=10,
                description="This active project has no tasks. Add tasks to establish an execution plan."
            ))
        return results


class RiskEngine:
    def __init__(self):
        self.rules = [
            ZeroTasksRule(),
            OverdueTaskRule(),
            TaskExceedsDeadlineRule(),
            DependencyBlockerRule(),
            ResourceOverloadRule(),
            TimelineProgressRule(),
            ProjectOverdueRule(),
        ]

    def _get_overloaded_users(self, active_projects) -> dict:
        """Helper to compute active task counts for all assignees across active projects."""
        # Avoid circular dependencies by local imports
        from tasks.models import Task
        
        # Aggregate active tasks grouped by assignee for active projects
        active_counts = Task.objects.filter(
            status__in=['todo', 'in_progress', 'review'],
            project__in=active_projects
        ).exclude(assignee__isnull=True).values('assignee').annotate(active_count=Count('id'))

        return {item['assignee']: item['active_count'] for item in active_counts if item['active_count'] >= 4}

    def analyze_project(self, project, today=None) -> ProjectRiskAnalysis:
        """Run analysis on a single project instance."""
        if not today:
            today = timezone.now().date()

        # Semantics check: Skip completed and planning projects
        if project.status == 'completed':
            return ProjectRiskAnalysis(project, 0, 'completed', [], [])
        if project.status == 'planning':
            return ProjectRiskAnalysis(project, 0, 'not_started', [], [])

        # Fetch active tasks
        active_tasks = [t for t in project.tasks.all() if t.status != 'done']

        # Resource overload context (single project scope calculation fallback)
        overloaded_users = {}
        # Avoid circular dependencies
        from tasks.models import Task
        from projects.models import Project
        
        active_counts = Task.objects.filter(
            status__in=['todo', 'in_progress', 'review'],
            project__status__in=['planning', 'active']
        ).exclude(assignee__isnull=True).values('assignee').annotate(active_count=Count('id'))
        overloaded_users = {item['assignee']: item['active_count'] for item in active_counts if item['active_count'] >= 4}

        context_data = {
            'overloaded_users': overloaded_users,
            'total_tasks_count': project.tasks.count()
        }

        # Run rules
        detected_risks = []
        for rule in self.rules:
            detected_risks.extend(rule.evaluate(project, active_tasks, today, context_data))

        # Scoring aggregation
        total_score = sum([r.score_addition for r in detected_risks])
        capped_score = min(100, total_score)

        # Status threshold mapping
        if capped_score < 30:
            status = 'on_track'
        elif capped_score < 60:
            status = 'at_risk'
        else:
            status = 'off_track'

        # Generate Actionable Recommendations
        recommendations = self._generate_recommendations(detected_risks)

        return ProjectRiskAnalysis(project, capped_score, status, detected_risks, recommendations)

    def analyze_multiple_projects(self, projects, today=None) -> List[ProjectRiskAnalysis]:
        """Optimized batch scan for multiple projects to prevent N+1 queries."""
        if not today:
            today = timezone.now().date()

        # Filter active projects to pass to resource overload check
        active_projects = [p for p in projects if p.status == 'active']
        overloaded_users = self._get_overloaded_users(active_projects)

        analyses = []
        for project in projects:
            # Semantics check
            if project.status == 'completed':
                analyses.append(ProjectRiskAnalysis(project, 0, 'completed', [], []))
                continue
            if project.status == 'planning':
                analyses.append(ProjectRiskAnalysis(project, 0, 'not_started', [], []))
                continue

            # Active tasks
            # We assume project.tasks.all() has been pre-fetched externally
            active_tasks = [t for t in project.tasks.all() if t.status != 'done']
            total_tasks_count = len(project.tasks.all())

            context_data = {
                'overloaded_users': overloaded_users,
                'total_tasks_count': total_tasks_count
            }

            # Run rules
            detected_risks = []
            for rule in self.rules:
                detected_risks.extend(rule.evaluate(project, active_tasks, today, context_data))

            # Aggregation
            total_score = sum([r.score_addition for r in detected_risks])
            capped_score = min(100, total_score)

            if capped_score < 30:
                status = 'on_track'
            elif capped_score < 60:
                status = 'at_risk'
            else:
                status = 'off_track'

            recommendations = self._generate_recommendations(detected_risks)
            analyses.append(ProjectRiskAnalysis(project, capped_score, status, detected_risks, recommendations))

        return analyses

    def _generate_recommendations(self, risks: List[RiskResult]) -> List[str]:
        recommendations = []
        
        # High priority items first (Rule F, Rule B, Rule E)
        for r in risks:
            if r.rule_code == 'rule_f':
                recommendations.append(f"Project timeline is overdue. Adjust project end date or mark the project as completed.")
            elif r.rule_code == 'rule_b':
                recommendations.append(f"Adjust deadline/due date of Task to resolve project end date conflict.")
            elif r.rule_code == 'rule_e':
                recommendations.append(f"Schedule timeline recovery check. Review project scope or allocate more team resources.")
            elif r.rule_code == 'rule_z':
                recommendations.append(f"This active project has no tasks. Add tasks to establish an execution plan.")

        # Medium/Low priority items (Rule A, Rule C, Rule D)
        for r in risks:
            if r.rule_code == 'rule_a':
                recommendations.append(f"Reassign overdue task or update its due date.")
            elif r.rule_code == 'rule_c':
                recommendations.append(f"Prioritize blocker task resolution to clear critical paths.")
            elif r.rule_code == 'rule_d':
                recommendations.append(f"Redistribute workload. Reassign tasks from overloaded team members.")
                
        # Return unique recommendations
        return list(dict.fromkeys(recommendations))

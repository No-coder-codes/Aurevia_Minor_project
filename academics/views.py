import csv
import io
import openpyxl
from django.db import models, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

from core.views import WorkspaceIsolatedMixin, get_active_workspace
from academics.models import (
    School,
    AcademicDepartment,
    AdministrativeDepartment,
    Programme,
    ClassDivision,
    Subject,
    FacultyProfile,
    TeachingAssignment,
    StudentProfile,
    ClassRepresentative,
    RoleAssignment,
    AdmissionsApplication,
    AdmissionsReview,
)
from tasks.models import Task
from academics.services import CollegeAccessPolicy

User = get_user_model()


class SchoolListView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    model = School
    template_name = 'academics/school_list.html'
    context_object_name = 'schools'

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return School.objects.none()
        return CollegeAccessPolicy.filter_schools(self.request.user, workspace)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workspace = get_active_workspace(self.request)
        context['workspace'] = workspace
        context['is_executive'] = CollegeAccessPolicy.is_institutional_executive(self.request.user, workspace) if workspace else False
        return context


class SchoolDetailView(WorkspaceIsolatedMixin, LoginRequiredMixin, DetailView):
    model = School
    template_name = 'academics/school_detail.html'
    context_object_name = 'school'

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return School.objects.none()
        return CollegeAccessPolicy.filter_schools(self.request.user, workspace)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workspace = get_active_workspace(self.request)
        school = self.get_object()
        departments = CollegeAccessPolicy.filter_academic_departments(self.request.user, workspace).filter(school=school)
        context['departments'] = departments
        return context


class AcademicDepartmentListView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    model = AcademicDepartment
    template_name = 'academics/department_list.html'
    context_object_name = 'departments'

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return AcademicDepartment.objects.none()
        return CollegeAccessPolicy.filter_academic_departments(self.request.user, workspace)


class AdministrativeDepartmentListView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    model = AdministrativeDepartment
    template_name = 'academics/admin_directory.html'
    context_object_name = 'departments'

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return AdministrativeDepartment.objects.none()
        return CollegeAccessPolicy.filter_administrative_departments(self.request.user, workspace)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workspace = get_active_workspace(self.request)
        context['workspace'] = workspace
        return context


class InstitutionalHierarchyView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    model = School
    template_name = 'academics/hierarchy_overview.html'
    context_object_name = 'schools'

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return School.objects.none()
        return CollegeAccessPolicy.filter_schools(self.request.user, workspace)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workspace = get_active_workspace(self.request)
        if workspace:
            context['admin_departments'] = CollegeAccessPolicy.filter_administrative_departments(self.request.user, workspace)
            context['leadership_roles'] = RoleAssignment.objects.filter(
                workspace=workspace,
                role__in=['president', 'provost', 'registrar']
            ).select_related('user')
        else:
            context['admin_departments'] = AdministrativeDepartment.objects.none()
            context['leadership_roles'] = RoleAssignment.objects.none()
        return context


# ==========================================
# PHASE 3: ACADEMIC MANAGEMENT VIEWS
# ==========================================

class ProgrammeListView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    """Lists degree programmes in the active workspace."""
    model = Programme
    template_name = 'academics/programme_list.html'
    context_object_name = 'programmes'

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return Programme.objects.none()
        return Programme.objects.filter(department__school__workspace=workspace).select_related('department', 'department__school', 'coordinator')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        programmes = list(context.get('programmes') or self.object_list or [])
        total_programmes = len(programmes)
        assigned_count = sum(1 for p in programmes if p.coordinator_id is not None)

        if total_programmes > 0:
            assignment_percentage = round((assigned_count / total_programmes) * 100)
        else:
            assignment_percentage = 0

        context['total_programmes'] = total_programmes
        context['assigned_coordinators_count'] = assigned_count
        context['assignment_percentage'] = assignment_percentage
        context['coordination_percentage'] = assignment_percentage
        context['ug_count'] = sum(1 for p in programmes if p.degree_level == 'undergraduate')
        context['pg_count'] = sum(1 for p in programmes if p.degree_level == 'postgraduate')
        return context


class ClassDivisionListView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    """Lists classes and divisions/sections."""
    model = ClassDivision
    template_name = 'academics/class_list.html'
    context_object_name = 'divisions'

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return ClassDivision.objects.none()
        return ClassDivision.objects.filter(programme__department__school__workspace=workspace).select_related('programme', 'programme__department')


class FacultyListView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    """Directory of faculty profiles and their designations."""
    model = FacultyProfile
    template_name = 'academics/faculty_list.html'
    context_object_name = 'faculty_members'

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return FacultyProfile.objects.none()
        return FacultyProfile.objects.filter(department__school__workspace=workspace).select_related('user', 'department')


class TeachingAssignmentListView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    """View of all faculty-subject-division teaching allocations."""
    model = TeachingAssignment
    template_name = 'academics/teaching_assignments.html'
    context_object_name = 'assignments'

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return TeachingAssignment.objects.none()
        user = self.request.user
        qs = TeachingAssignment.objects.filter(division__programme__department__school__workspace=workspace).select_related('faculty__user', 'subject', 'division', 'division__programme')
        
        # If user is a faculty member without executive authority, show their own assignments
        if not CollegeAccessPolicy.is_institutional_executive(user, workspace):
            if hasattr(user, 'faculty_profile'):
                qs = qs.filter(faculty=user.faculty_profile)
        return qs


class StudentRosterView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    """Student roster with division and programme filtering."""
    model = StudentProfile
    template_name = 'academics/student_roster.html'
    context_object_name = 'students'
    ordering = ['student_id']
    paginate_by = 50

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return StudentProfile.objects.none()
        
        user = self.request.user
        qs = StudentProfile.objects.filter(programme__department__school__workspace=workspace).select_related('user', 'programme', 'division')
        
        # CR Access check: If user is CR, strictly restrict roster to their assigned class division
        if hasattr(user, 'student_profile') and hasattr(user.student_profile, 'cr_role') and user.student_profile.cr_role.is_active:
            cr_division = user.student_profile.cr_role.division
            if not CollegeAccessPolicy.is_institutional_executive(user, workspace):
                qs = qs.filter(division=cr_division)

        # Filters
        prog_id = self.request.GET.get('programme')
        div_id = self.request.GET.get('division')
        search = self.request.GET.get('q')

        if prog_id:
            qs = qs.filter(programme_id=prog_id)
        if div_id:
            qs = qs.filter(division_id=div_id)
        if search:
            qs = qs.filter(
                models.Q(student_id__icontains=search) |
                models.Q(user__first_name__icontains=search) |
                models.Q(user__last_name__icontains=search) |
                models.Q(user__username__icontains=search)
            )
        return qs.order_by('student_id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workspace = get_active_workspace(self.request)
        if workspace:
            context['programmes'] = Programme.objects.filter(department__school__workspace=workspace)
            context['divisions'] = ClassDivision.objects.filter(programme__department__school__workspace=workspace)
        return context


class ClassRepresentativePortalView(WorkspaceIsolatedMixin, LoginRequiredMixin, DetailView):
    """Dedicated portal for a Class Representative (CR) scoped strictly to their assigned division."""
    model = ClassDivision
    template_name = 'academics/cr_portal.html'
    context_object_name = 'division'

    def get_object(self):
        workspace = get_active_workspace(self.request)
        user = self.request.user
        
        # Check if user is CR
        if hasattr(user, 'student_profile') and hasattr(user.student_profile, 'cr_role'):
            cr = user.student_profile.cr_role
            if cr.is_active and cr.division.programme.department.school.workspace == workspace:
                return cr.division
                
        # If user is executive, allow viewing by pk or first division
        if CollegeAccessPolicy.is_institutional_executive(user, workspace):
            pk = self.kwargs.get('pk')
            if pk:
                return get_object_or_404(ClassDivision, pk=pk, programme__department__school__workspace=workspace)
            div = ClassDivision.objects.filter(programme__department__school__workspace=workspace).first()
            if div:
                return div
        
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("You do not have active Class Representative authorization for any division.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        division = self.get_object()
        context['class_roster'] = StudentProfile.objects.filter(division=division).select_related('user')
        context['teaching_faculty'] = TeachingAssignment.objects.filter(division=division).select_related('faculty__user', 'subject')
        return context


class StudentRosterImportView(WorkspaceIsolatedMixin, LoginRequiredMixin, View):
    """
    Authorized bulk CSV/Excel student roster import.
    Features:
      - Validates file type (.csv, .xlsx) and size (< 5MB)
      - Row-by-row validation with preview and error log
      - Atomic transaction to prevent partial corrupt imports
      - Formula injection protection (openpyxl data-only mode)
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        workspace = get_active_workspace(request)
        if not workspace or hasattr(request.user, 'student_profile'):
            raise PermissionDenied("Students are not authorized to access student roster import.")
        if not CollegeAccessPolicy.is_institutional_executive(request.user, workspace):
            raise PermissionDenied("Only institutional executives and administrators can import student rosters.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        workspace = get_active_workspace(request)
        programmes = Programme.objects.filter(department__school__workspace=workspace)
        divisions = ClassDivision.objects.filter(programme__department__school__workspace=workspace)
        return render(request, 'academics/roster_import.html', {
            'programmes': programmes,
            'divisions': divisions,
        })

    def post(self, request):
        workspace = get_active_workspace(request)
        if not CollegeAccessPolicy.is_institutional_executive(request.user, workspace):
            messages.error(request, "Permission denied. Only authorized administrators can import student rosters.")
            return redirect('academics:student_roster')

        uploaded_file = request.FILES.get('roster_file')
        if not uploaded_file:
            messages.error(request, "Please select a valid CSV or Excel file to import.")
            return redirect('academics:roster_import')

        if uploaded_file.size > 5 * 1024 * 1024:
            messages.error(request, "File size exceeds the 5MB maximum limit.")
            return redirect('academics:roster_import')

        filename = uploaded_file.name.lower()
        rows = []
        errors = []

        try:
            if filename.endswith('.csv'):
                decoded_file = uploaded_file.read().decode('utf-8-sig')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                for idx, row in enumerate(reader, start=2):
                    rows.append((idx, row))
            elif filename.endswith('.xlsx'):
                wb = openpyxl.load_workbook(uploaded_file, data_only=True)
                ws = wb.active
                headers = [str(cell.value).strip() if cell.value is not None else '' for cell in ws[1]]
                for idx, row_cells in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                    row_dict = dict(zip(headers, row_cells))
                    rows.append((idx, row_dict))
            else:
                messages.error(request, "Unsupported file format. Please upload a .csv or .xlsx spreadsheet.")
                return redirect('academics:roster_import')
        except Exception as e:
            messages.error(request, f"Error parsing uploaded file: {str(e)}")
            return redirect('academics:roster_import')

        # Dry-run validation
        validated_students = []
        existing_student_ids = set(StudentProfile.objects.values_list('student_id', flat=True))
        existing_usernames = set(User.objects.values_list('username', flat=True))
        seen_in_batch = set()

        for line_num, data in rows:
            student_id = str(data.get('student_id') or data.get('Student ID') or '').strip()
            username = str(data.get('username') or data.get('Username') or '').strip()
            first_name = str(data.get('first_name') or data.get('First Name') or '').strip()
            last_name = str(data.get('last_name') or data.get('Last Name') or '').strip()
            email = str(data.get('email') or data.get('Email') or '').strip()
            prog_code = str(data.get('programme_code') or data.get('Programme') or '').strip()
            div_name = str(data.get('division_name') or data.get('Division') or '').strip()

            if not student_id or not username or not email:
                errors.append(f"Row {line_num}: student_id, username, and email are required fields.")
                continue

            if student_id in existing_student_ids or student_id in seen_in_batch:
                errors.append(f"Row {line_num}: Duplicate student ID '{student_id}'.")
                continue

            if username in existing_usernames:
                errors.append(f"Row {line_num}: Username '{username}' already exists.")
                continue

            # Resolve Programme in workspace
            programme = Programme.objects.filter(department__school__workspace=workspace, code__iexact=prog_code).first()
            if not programme:
                errors.append(f"Row {line_num}: Programme code '{prog_code}' not found in current campus.")
                continue

            # Resolve Division (optional or matched)
            division = None
            if div_name:
                division = ClassDivision.objects.filter(programme=programme, name__iexact=div_name).first()

            seen_in_batch.add(student_id)
            validated_students.append({
                'student_id': student_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'programme': programme,
                'division': division,
            })

        # If any validation errors occurred, reject import cleanly
        if errors:
            return render(request, 'academics/roster_import.html', {
                'errors': errors,
                'total_rows': len(rows),
                'successful_rows': 0,
            })

        # Atomic database insertion
        try:
            with transaction.atomic():
                created_count = 0
                for item in validated_students:
                    user = User.objects.create_user(
                        username=item['username'],
                        email=item['email'],
                        first_name=item['first_name'],
                        last_name=item['last_name'],
                        password='ChangeMe123!',
                        role='team_member',
                    )
                    StudentProfile.objects.create(
                        user=user,
                        student_id=item['student_id'],
                        programme=item['programme'],
                        division=item['division'],
                        current_semester=item['division'].semester if item['division'] else 1,
                        enrollment_status='active',
                    )
                    created_count += 1
                messages.success(request, f"Successfully imported {created_count} student records.")
                return redirect('academics:student_roster')
        except Exception as e:
            messages.error(request, f"Database transaction failed: {str(e)}")
            return redirect('academics:roster_import')


# ==========================================
# PHASE 4: ADMINISTRATIVE & ADMISSIONS VIEWS
# ==========================================

class AdministrativeDepartmentDetailView(WorkspaceIsolatedMixin, LoginRequiredMixin, DetailView):
    """Detail view for an administrative department (Hostels, IT, Admissions, Finance)."""
    model = AdministrativeDepartment
    template_name = 'academics/admin_detail.html'
    context_object_name = 'dept'

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return AdministrativeDepartment.objects.none()
        return CollegeAccessPolicy.filter_administrative_departments(self.request.user, workspace)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workspace = get_active_workspace(self.request)
        dept = self.get_object()
        
        # Associated staff role assignments
        context['staff_roles'] = RoleAssignment.objects.filter(admin_dept=dept).select_related('user')
        
        # Operational tasks linked to this administrative domain
        tasks_qs = Task.objects.filter(project__workspace=workspace)
        if dept.category in ['boys_hostel', 'girls_hostel']:
            context['facility_tasks'] = tasks_qs.filter(
                models.Q(title__icontains='hostel') | models.Q(description__icontains=dept.name) | models.Q(description__icontains='room') | models.Q(description__icontains='maintenance')
            )[:10]
        elif dept.category == 'it':
            context['facility_tasks'] = tasks_qs.filter(
                models.Q(title__icontains='it') | models.Q(title__icontains='server') | models.Q(title__icontains='network') | models.Q(title__icontains='wifi')
            )[:10]
        elif dept.category == 'admissions':
            context['admissions_summary'] = {
                'total': AdmissionsApplication.objects.filter(workspace=workspace).count(),
                'pending_admin': AdmissionsApplication.objects.filter(workspace=workspace, status__in=['submitted', 'admin_review']).count(),
                'pending_academic': AdmissionsApplication.objects.filter(workspace=workspace, status='academic_review').count(),
                'approved': AdmissionsApplication.objects.filter(workspace=workspace, status='approved').count(),
            }
        return context


def check_admissions_access(user, workspace):
    """
    Validates whether the user has legitimate operational, executive, or academic review authority
    over admissions applications. Students and unauthorized accounts are strictly forbidden.
    """
    if not user.is_authenticated:
        return False
    if hasattr(user, 'student_profile'):
        return False
    if CollegeAccessPolicy.is_institutional_executive(user, workspace):
        return True
    if CollegeAccessPolicy.can_manage_admissions_admin(user, workspace):
        return True
    if CollegeAccessPolicy.filter_academic_departments(user, workspace).exists():
        return True
    if AdmissionsApplication.objects.filter(workspace=workspace, assigned_academic_reviewer=user).exists():
        return True
    return False


class AdmissionsApplicationListView(WorkspaceIsolatedMixin, LoginRequiredMixin, ListView):
    """
    Admissions applications management list.
    Displays applications, allows filtering by status & programme, and summarizes pipeline counts.
    """
    model = AdmissionsApplication
    template_name = 'academics/admissions_list.html'
    context_object_name = 'applications'
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        workspace = get_active_workspace(request)
        if not workspace or not check_admissions_access(request.user, workspace):
            raise PermissionDenied("You do not have authorization to access admissions management.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return AdmissionsApplication.objects.none()
        
        user = self.request.user
        qs = AdmissionsApplication.objects.filter(workspace=workspace).select_related(
            'targeted_programme', 'targeted_programme__department', 'assigned_admin', 'assigned_academic_reviewer'
        )

        # Scoped access for academic reviewers who are not executives
        if not CollegeAccessPolicy.can_manage_admissions_admin(user, workspace) and not CollegeAccessPolicy.is_institutional_executive(user, workspace):
            # Faculty/Reviewer only sees applications for programmes under their scope
            accessible_depts = CollegeAccessPolicy.filter_academic_departments(user, workspace)
            qs = qs.filter(
                models.Q(targeted_programme__department__in=accessible_depts) |
                models.Q(assigned_academic_reviewer=user)
            )

        status_filter = self.request.GET.get('status')
        prog_filter = self.request.GET.get('programme')
        search = self.request.GET.get('q')

        if status_filter:
            qs = qs.filter(status=status_filter)
        if prog_filter:
            qs = qs.filter(targeted_programme_id=prog_filter)
        if search:
            qs = qs.filter(
                models.Q(application_number__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search)
            )
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workspace = get_active_workspace(self.request)
        user = self.request.user
        if workspace:
            context['programmes'] = Programme.objects.filter(department__school__workspace=workspace)
            all_apps = AdmissionsApplication.objects.filter(workspace=workspace)
            context['metrics'] = {
                'total': all_apps.count(),
                'submitted': all_apps.filter(status='submitted').count(),
                'admin_review': all_apps.filter(status='admin_review').count(),
                'academic_review': all_apps.filter(status='academic_review').count(),
                'approved': all_apps.filter(status='approved').count(),
                'rejected': all_apps.filter(status='rejected').count(),
            }
            context['can_admin_admissions'] = CollegeAccessPolicy.can_manage_admissions_admin(user, workspace)
            context['can_finalize'] = CollegeAccessPolicy.can_finalize_admission(user, workspace)
        return context


class AdmissionsApplicationDetailView(WorkspaceIsolatedMixin, LoginRequiredMixin, DetailView):
    """
    Admissions detail view with complete dual-reporting history and role-scoped action panels.
    - Registrar/Admissions Officer: Administrative Verification.
    - Academic Reviewer: Academic Evaluation.
    - Institutional Leadership: Final Approval/Rejection.
    """
    model = AdmissionsApplication
    template_name = 'academics/admissions_detail.html'
    context_object_name = 'application'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        workspace = get_active_workspace(request)
        if not workspace or not check_admissions_access(request.user, workspace):
            raise PermissionDenied("You do not have authorization to access admissions records.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        workspace = get_active_workspace(self.request)
        if not workspace:
            return AdmissionsApplication.objects.none()
        return AdmissionsApplication.objects.filter(workspace=workspace).select_related(
            'targeted_programme', 'targeted_programme__department', 'assigned_admin', 'assigned_academic_reviewer'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workspace = get_active_workspace(self.request)
        user = self.request.user
        app = self.get_object()

        context['reviews'] = app.reviews.select_related('reviewer').order_by('-created_at')
        context['can_admin_verify'] = CollegeAccessPolicy.can_manage_admissions_admin(user, workspace)
        context['can_academic_review'] = CollegeAccessPolicy.can_review_admissions_academic(user, workspace, app)
        context['can_finalize'] = CollegeAccessPolicy.can_finalize_admission(user, workspace)
        context['available_reviewers'] = User.objects.filter(
            workspace_memberships__workspace=workspace,
            role__in=['project_manager', 'director', 'team_lead']
        ).distinct()
        return context


class AdmissionsActionView(WorkspaceIsolatedMixin, LoginRequiredMixin, View):
    """Processes stage-specific actions (Admin Verification, Academic Review, Final Decision)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        workspace = get_active_workspace(request)
        if not workspace or hasattr(request.user, 'student_profile'):
            raise PermissionDenied("Students cannot execute admissions actions.")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        workspace = get_active_workspace(request)
        application = get_object_or_404(AdmissionsApplication, pk=pk, workspace=workspace)
        action_type = request.POST.get('action_type')
        user = request.user

        if action_type == 'admin_verify':
            if not CollegeAccessPolicy.can_manage_admissions_admin(user, workspace):
                messages.error(request, "Permission denied: Only Registrar/Admissions staff can perform administrative verification.")
                return redirect('academics:admissions_detail', pk=pk)

            decision = request.POST.get('decision', 'recommended')
            comments = request.POST.get('comments', '').strip()
            reviewer_id = request.POST.get('assigned_academic_reviewer')
            
            if reviewer_id:
                application.assigned_academic_reviewer_id = reviewer_id

            if decision == 'approved_for_academic':
                application.status = 'academic_review'
            else:
                application.status = 'admin_review'
            
            application.assigned_admin = user
            application.save()

            AdmissionsReview.objects.create(
                application=application,
                reviewer=user,
                stage='admin',
                decision='recommended' if decision == 'approved_for_academic' else 'info_required',
                comments=comments or "Administrative documents verified and routed for academic evaluation."
            )
            messages.success(request, f"Administrative verification recorded for application #{application.application_number}.")

        elif action_type == 'academic_review':
            if not CollegeAccessPolicy.can_review_admissions_academic(user, workspace, application):
                messages.error(request, "Permission denied: You are not authorized to record academic reviews for this programme.")
                return redirect('academics:admissions_detail', pk=pk)

            decision = request.POST.get('decision', 'recommended')
            comments = request.POST.get('comments', '').strip()

            AdmissionsReview.objects.create(
                application=application,
                reviewer=user,
                stage='academic',
                decision=decision,
                comments=comments
            )
            messages.success(request, f"Academic review recommendation ({decision}) submitted.")

        elif action_type == 'finalize':
            if not CollegeAccessPolicy.can_finalize_admission(user, workspace):
                messages.error(request, "Permission denied: Only authorized executive leadership can issue final admission decisions.")
                return redirect('academics:admissions_detail', pk=pk)

            final_decision = request.POST.get('final_decision')
            comments = request.POST.get('comments', '').strip()

            if final_decision in ['approved', 'rejected']:
                application.status = final_decision
                application.save()
                AdmissionsReview.objects.create(
                    application=application,
                    reviewer=user,
                    stage='academic',
                    decision='approved' if final_decision == 'approved' else 'rejected',
                    comments=comments or f"Final decision: {final_decision.capitalize()} by executive office."
                )
                messages.success(request, f"Application #{application.application_number} marked as {final_decision.upper()}.")
            else:
                messages.error(request, "Invalid final decision selection.")

        return redirect('academics:admissions_detail', pk=pk)


class AdmissionsApplicationCreateView(WorkspaceIsolatedMixin, LoginRequiredMixin, View):
    """Allows authorized staff to register a new candidate application."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        workspace = get_active_workspace(request)
        if not workspace or hasattr(request.user, 'student_profile') or not CollegeAccessPolicy.can_manage_admissions_admin(request.user, workspace):
            raise PermissionDenied("Only authorized admissions staff can register candidate applications.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        workspace = get_active_workspace(request)
        if not CollegeAccessPolicy.can_manage_admissions_admin(request.user, workspace):
            messages.error(request, "Permission denied: Only Admissions officers can create applications.")
            return redirect('academics:admissions_list')
        
        programmes = Programme.objects.filter(department__school__workspace=workspace)
        return render(request, 'academics/admissions_create.html', {'programmes': programmes})

    def post(self, request):
        workspace = get_active_workspace(request)
        if not CollegeAccessPolicy.can_manage_admissions_admin(request.user, workspace):
            messages.error(request, "Permission denied.")
            return redirect('academics:admissions_list')

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        prog_id = request.POST.get('programme')

        if not (first_name and last_name and email and prog_id):
            messages.error(request, "Please fill in all required candidate fields.")
            return redirect('academics:admissions_create')

        programme = get_object_or_404(Programme, pk=prog_id, department__school__workspace=workspace)
        import random
        app_num = f"APP-2026-{random.randint(10000, 99999)}"

        app = AdmissionsApplication.objects.create(
            workspace=workspace,
            application_number=app_num,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            targeted_programme=programme,
            status='submitted',
            assigned_admin=request.user
        )
        messages.success(request, f"Candidate application #{app.application_number} registered successfully.")
        return redirect('academics:admissions_detail', pk=app.pk)


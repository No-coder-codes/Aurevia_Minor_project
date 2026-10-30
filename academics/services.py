from typing import Optional, List
from django.db import models
from django.db.models import QuerySet
from core.models import User, Workspace
from academics.models import (
    School,
    AcademicDepartment,
    AdministrativeDepartment,
    Programme,
    ClassDivision,
    RoleAssignment,
)

class CollegeAccessPolicy:
    """
    Enforces server-side scoped permissions across the institutional hierarchy.
    Roles:
      - president: Full institutional overview across all schools & departments
      - provost: Academic Affairs overview (all schools, programmes, divisions)
      - registrar: Non-Academic Affairs overview (all administrative departments)
      - dean: Scoped to their assigned School (and its departments/programmes)
      - hod: Scoped to their assigned AcademicDepartment (and its programmes)
      - coordinator: Scoped to their assigned Programme (and its divisions)
      - admin_head / admin_staff: Scoped to their assigned AdministrativeDepartment
    """

    @staticmethod
    def get_user_roles(user: User, workspace: Workspace) -> QuerySet[RoleAssignment]:
        if not user.is_authenticated:
            return RoleAssignment.objects.none()
        return RoleAssignment.objects.filter(user=user, workspace=workspace)

    @classmethod
    def is_institutional_executive(cls, user: User, workspace: Workspace) -> bool:
        """President, Director or Workspace Owner/Admin has global institutional view within the workspace."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        # User must belong to this specific workspace to be an institutional executive for it
        if not user.workspace_memberships.filter(workspace=workspace).exists():
            return False
        if user.role == 'director':
            return True
        return cls.get_user_roles(user, workspace).filter(
            role__in=['president', 'provost', 'registrar']
        ).exists()

    @classmethod
    def filter_schools(cls, user: User, workspace: Workspace) -> QuerySet[School]:
        qs = School.objects.filter(workspace=workspace)
        if not user.is_authenticated:
            return qs.none()
        if cls.is_institutional_executive(user, workspace):
            return qs

        roles = cls.get_user_roles(user, workspace)
        # Provost has full academic school access
        if roles.filter(role__in=['provost', 'president']).exists():
            return qs
        # Dean has access to their specific school
        dean_schools = roles.filter(role='dean', school__isnull=False).values_list('school_id', flat=True)
        # Direct dean FK
        direct_dean = qs.filter(dean=user).values_list('id', flat=True)
        # HoD has access to the school of their department
        hod_depts = roles.filter(role='hod', academic_dept__isnull=False).values_list('academic_dept__school_id', flat=True)

        allowed_ids = set(dean_schools) | set(direct_dean) | set(hod_depts)
        return qs.filter(id__in=allowed_ids)

    @classmethod
    def filter_academic_departments(cls, user: User, workspace: Workspace) -> QuerySet[AcademicDepartment]:
        qs = AcademicDepartment.objects.filter(school__workspace=workspace)
        if not user.is_authenticated:
            return qs.none()
        if cls.is_institutional_executive(user, workspace):
            return qs

        roles = cls.get_user_roles(user, workspace)
        if roles.filter(role__in=['provost', 'president']).exists():
            return qs

        # Deans see all departments under their assigned school
        dean_schools = roles.filter(role='dean', school__isnull=False).values_list('school_id', flat=True)
        direct_dean_schools = School.objects.filter(workspace=workspace, dean=user).values_list('id', flat=True)
        all_dean_schools = set(dean_schools) | set(direct_dean_schools)

        # HoD sees their specific department
        hod_depts = roles.filter(role='hod', academic_dept__isnull=False).values_list('academic_dept_id', flat=True)
        direct_hod = qs.filter(hod=user).values_list('id', flat=True)
        all_hod_depts = set(hod_depts) | set(direct_hod)

        return qs.filter(
            models.Q(school_id__in=all_dean_schools) | models.Q(id__in=all_hod_depts)
        )

    @classmethod
    def filter_administrative_departments(cls, user: User, workspace: Workspace) -> QuerySet[AdministrativeDepartment]:
        qs = AdministrativeDepartment.objects.filter(workspace=workspace)
        if not user.is_authenticated:
            return qs.none()
        if cls.is_institutional_executive(user, workspace):
            return qs

        roles = cls.get_user_roles(user, workspace)
        # Registrar has full administrative directory access
        if roles.filter(role__in=['registrar', 'president']).exists():
            return qs

        # Department heads / staff see their assigned admin department
        admin_depts = roles.filter(
            role__in=['admin_head', 'admin_staff', 'admissions_officer'],
            admin_dept__isnull=False
        ).values_list('admin_dept_id', flat=True)
        direct_head = qs.filter(head=user).values_list('id', flat=True)

        allowed_ids = set(admin_depts) | set(direct_head)
        return qs.filter(id__in=allowed_ids)

    @classmethod
    def can_manage_admissions_admin(cls, user: User, workspace: Workspace) -> bool:
        """Determines if user has Registrar/Admissions Office operational processing authority."""
        if not user.is_authenticated:
            return False
        if cls.is_institutional_executive(user, workspace):
            return True
        roles = cls.get_user_roles(user, workspace)
        return roles.filter(role__in=['registrar', 'admissions_officer', 'admin_staff']).exists()

    @classmethod
    def can_review_admissions_academic(cls, user: User, workspace: Workspace, application=None) -> bool:
        """Determines if user has academic review authority for an application."""
        if not user.is_authenticated:
            return False
        if cls.is_institutional_executive(user, workspace):
            return True
        roles = cls.get_user_roles(user, workspace)
        if roles.filter(role__in=['provost', 'academic_reviewer']).exists():
            return True
        if application and hasattr(application, 'targeted_programme'):
            target_school = application.targeted_programme.department.school
            target_dept = application.targeted_programme.department
            # Dean of target school
            if roles.filter(role='dean', school=target_school).exists() or target_school.dean == user:
                return True
            # HoD of target department
            if roles.filter(role='hod', academic_dept=target_dept).exists() or target_dept.hod == user:
                return True
            # Assigned academic reviewer direct FK
            if application.assigned_academic_reviewer == user:
                return True
        return False

    @classmethod
    def can_finalize_admission(cls, user: User, workspace: Workspace) -> bool:
        """Determines if user can issue final admission approval/rejection."""
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.role == 'director':
            return True
        roles = cls.get_user_roles(user, workspace)
        return roles.filter(role__in=['president', 'provost', 'registrar']).exists()


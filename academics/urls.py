from django.urls import path
from academics.views import (
    InstitutionalHierarchyView,
    SchoolListView,
    SchoolDetailView,
    AcademicDepartmentListView,
    AdministrativeDepartmentListView,
    ProgrammeListView,
    ClassDivisionListView,
    FacultyListView,
    TeachingAssignmentListView,
    StudentRosterView,
    ClassRepresentativePortalView,
    StudentRosterImportView,
    AdministrativeDepartmentDetailView,
    AdmissionsApplicationListView,
    AdmissionsApplicationDetailView,
    AdmissionsActionView,
    AdmissionsApplicationCreateView,
)

app_name = 'academics'

urlpatterns = [
    # Hierarchy & Directories
    path('hierarchy/', InstitutionalHierarchyView.as_view(), name='hierarchy_overview'),
    path('schools/', SchoolListView.as_view(), name='school_list'),
    path('schools/<int:pk>/', SchoolDetailView.as_view(), name='school_detail'),
    path('departments/', AcademicDepartmentListView.as_view(), name='department_list'),
    path('admin-directory/', AdministrativeDepartmentListView.as_view(), name='admin_directory'),
    path('admin-directory/<int:pk>/', AdministrativeDepartmentDetailView.as_view(), name='admin_detail'),

    # Phase 3 Academic Management
    path('programmes/', ProgrammeListView.as_view(), name='programme_list'),
    path('classes/', ClassDivisionListView.as_view(), name='class_list'),
    path('faculty/', FacultyListView.as_view(), name='faculty_list'),
    path('teaching-assignments/', TeachingAssignmentListView.as_view(), name='teaching_assignments'),
    path('students/', StudentRosterView.as_view(), name='student_roster'),
    path('cr-portal/', ClassRepresentativePortalView.as_view(), name='cr_portal'),
    path('cr-portal/<int:pk>/', ClassRepresentativePortalView.as_view(), name='cr_portal_detail'),
    path('students/import/', StudentRosterImportView.as_view(), name='roster_import'),

    # Phase 4 Administrative & Admissions Workflow
    path('admissions/', AdmissionsApplicationListView.as_view(), name='admissions_list'),
    path('admissions/create/', AdmissionsApplicationCreateView.as_view(), name='admissions_create'),
    path('admissions/<int:pk>/', AdmissionsApplicationDetailView.as_view(), name='admissions_detail'),
    path('admissions/<int:pk>/action/', AdmissionsActionView.as_view(), name='admissions_action'),
]

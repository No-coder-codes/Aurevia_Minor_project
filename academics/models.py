from django.db import models
from django.conf import settings
from core.models import Workspace

class School(models.Model):
    """Academic School (e.g., School of Engineering, School of Business)."""
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='schools')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    dean = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_schools'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ('workspace', 'code')

    def __str__(self):
        return f"{self.name} ({self.code})"


class AcademicDepartment(models.Model):
    """Academic Department (e.g., Computer Science, Electrical Engineering)."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    hod = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_academic_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ('school', 'code')

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.school.name}"


class AdministrativeDepartment(models.Model):
    """Non-Academic / Administrative Department reporting to Registrar or Provost."""
    CATEGORY_CHOICES = (
        ('finance', 'Finance & Accounts'),
        ('admin', 'Administration'),
        ('it', 'IT Department / Services'),
        ('boys_hostel', "Boys' Hostel"),
        ('girls_hostel', "Girls' Hostel"),
        ('hr', 'HR / Establishment'),
        ('library', 'Library & Learning Resources'),
        ('maintenance', 'Estate & Maintenance'),
        ('admissions', 'Admissions Coordination Office'),
        ('other', 'Other Administrative Unit'),
    )

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='admin_departments')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    head = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_admin_departments'
    )
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True, help_text="Capacity for residential hostels or facilities")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ('workspace', 'code')

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Programme(models.Model):
    """Degree or Diploma Programme (e.g. B.Tech Computer Science, MBA)."""
    DEGREE_CHOICES = (
        ('undergraduate', 'Undergraduate (UG)'),
        ('postgraduate', 'Postgraduate (PG)'),
        ('doctoral', 'Doctoral (PhD)'),
        ('diploma', 'Diploma / Certificate'),
    )

    department = models.ForeignKey(AcademicDepartment, on_delete=models.CASCADE, related_name='programmes')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    degree_level = models.CharField(max_length=30, choices=DEGREE_CHOICES, default='undergraduate')
    duration_years = models.PositiveSmallIntegerField(default=4)
    total_semesters = models.PositiveSmallIntegerField(default=8)
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coordinated_programmes'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ('department', 'code')

    def __str__(self):
        return f"{self.name} ({self.code})"


class ClassDivision(models.Model):
    """Section / Division of a class (e.g. B.Tech CSE Year 3 Sem 5 Section A)."""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='divisions')
    name = models.CharField(max_length=50, help_text="e.g. Section A, Section B")
    academic_year = models.CharField(max_length=20, help_text="e.g. 2026-2027")
    semester = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['programme', 'semester', 'name']
        unique_together = ('programme', 'academic_year', 'semester', 'name')

    def __str__(self):
        return f"{self.programme.code} - Sem {self.semester} {self.name} ({self.academic_year})"


class Subject(models.Model):
    """Academic subject / course module."""
    department = models.ForeignKey(AcademicDepartment, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    credits = models.PositiveSmallIntegerField(default=3)
    semester_recommended = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['code']
        unique_together = ('department', 'code')

    def __str__(self):
        return f"{self.code} - {self.name} ({self.credits} Credits)"


class FacultyProfile(models.Model):
    """Profile for faculty members."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='faculty_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(AcademicDepartment, on_delete=models.SET_NULL, null=True, related_name='faculty_members')
    designation = models.CharField(max_length=100, default='Assistant Professor')
    phone = models.CharField(max_length=50, blank=True)
    office_location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.designation} ({self.department.code if self.department else 'Unassigned'})"


class TeachingAssignment(models.Model):
    """Many-to-many allocation of faculty to subjects and class divisions."""
    faculty = models.ForeignKey(FacultyProfile, on_delete=models.CASCADE, related_name='teaching_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assignments')
    division = models.ForeignKey(ClassDivision, on_delete=models.CASCADE, related_name='teaching_assignments')
    academic_year = models.CharField(max_length=20, default='2026-2027')
    schedule_details = models.CharField(max_length=255, blank=True, help_text="e.g. Mon/Wed/Fri 10:00 - 11:00 AM")

    class Meta:
        unique_together = ('faculty', 'subject', 'division', 'academic_year')

    def __str__(self):
        return f"{self.faculty.user.username} teaches {self.subject.code} in {self.division}"


class StudentProfile(models.Model):
    """Profile for students."""
    ENROLLMENT_STATUS = (
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('graduated', 'Graduated'),
        ('withdrawn', 'Withdrawn'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True)
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='students')
    division = models.ForeignKey(ClassDivision, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    current_semester = models.PositiveSmallIntegerField(default=1)
    phone = models.CharField(max_length=50, blank=True)
    enrollment_status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='active')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.student_id}) - {self.programme.code}"


class ClassRepresentative(models.Model):
    """Designation for a student serving as Class Representative (CR) for a division."""
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='cr_role')
    division = models.ForeignKey(ClassDivision, on_delete=models.CASCADE, related_name='representatives')
    appointed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"CR {self.student.user.username} for {self.division}"


class RoleAssignment(models.Model):
    """Scoped institutional role assignment for users."""
    INSTITUTIONAL_ROLES = (
        ('president', 'President'),
        ('provost', 'Vice-Chancellor / Provost'),
        ('registrar', 'Registrar'),
        ('dean', 'Dean'),
        ('hod', 'Head of Department (HoD)'),
        ('coordinator', 'Programme Coordinator'),
        ('faculty', 'Faculty Member'),
        ('cr', 'Class Representative (CR)'),
        ('student', 'Student'),
        ('admin_head', 'Administrative Department Head'),
        ('admin_staff', 'Administrative Staff'),
        ('admissions_officer', 'Admissions Officer'),
        ('academic_reviewer', 'Academic Reviewer'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='institutional_roles')
    role = models.CharField(max_length=30, choices=INSTITUTIONAL_ROLES)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='institutional_role_assignments')
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_roles')
    academic_dept = models.ForeignKey(AcademicDepartment, on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_roles')
    admin_dept = models.ForeignKey(AdministrativeDepartment, on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_roles')
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_roles')
    division = models.ForeignKey(ClassDivision, on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_roles')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        scope_str = self.school or self.academic_dept or self.admin_dept or self.programme or self.division or self.workspace
        return f"{self.user.username} -> {self.get_role_display()} [{scope_str}]"


class AdmissionsApplication(models.Model):
    """Dual-reporting Admissions Application linking Registrar processing and Academic Review."""
    STATUS_CHOICES = (
        ('submitted', 'Application Submitted'),
        ('admin_review', 'Administrative Verification'),
        ('academic_review', 'Academic Review in Progress'),
        ('approved', 'Approved for Admission'),
        ('rejected', 'Application Rejected'),
    )

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='admissions_applications')
    application_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    targeted_programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='admissions_applications')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='submitted')
    assigned_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_admissions'
    )
    assigned_academic_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_admissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.application_number}: {self.first_name} {self.last_name} ({self.targeted_programme.code})"


class AdmissionsReview(models.Model):
    """Review log and audit record for an application step."""
    application = models.ForeignKey(AdmissionsApplication, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stage = models.CharField(max_length=30, choices=(('admin', 'Administrative Verification'), ('academic', 'Academic Recommendation')))
    decision = models.CharField(max_length=30, choices=(('recommended', 'Recommended'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('info_required', 'More Info Required')))
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.application.application_number} ({self.decision})"

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import User, Organization, Workspace, WorkspaceMembership
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
from projects.models import Project
from tasks.models import Task
from academics.services import CollegeAccessPolicy

class CollegeHierarchyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(name="NexusFlow University Org")
        self.ws_main = Workspace.objects.create(name="Main Campus", slug="main-campus", organization=self.org)
        self.ws_other = Workspace.objects.create(name="Other Campus", slug="other-campus", organization=self.org)

        # Users
        self.director = User.objects.create_user(username="director_user", password="password123", role="director")
        self.dean_eng = User.objects.create_user(username="dean_eng", password="password123", role="project_manager")
        self.dean_biz = User.objects.create_user(username="dean_biz", password="password123", role="project_manager")
        self.reg_user = User.objects.create_user(username="registrar_user", password="password123", role="project_manager")
        self.student = User.objects.create_user(username="student_user", password="password123", role="team_member")

        # Memberships
        WorkspaceMembership.objects.create(user=self.director, workspace=self.ws_main, role="owner")
        WorkspaceMembership.objects.create(user=self.dean_eng, workspace=self.ws_main, role="admin")
        WorkspaceMembership.objects.create(user=self.dean_biz, workspace=self.ws_main, role="project_manager")
        WorkspaceMembership.objects.create(user=self.reg_user, workspace=self.ws_main, role="admin")
        WorkspaceMembership.objects.create(user=self.student, workspace=self.ws_main, role="team_member")

        # Schools in Main Campus
        self.school_eng = School.objects.create(
            workspace=self.ws_main, name="School of Engineering", code="ENG", dean=self.dean_eng
        )
        self.school_biz = School.objects.create(
            workspace=self.ws_main, name="School of Business", code="BIZ", dean=self.dean_biz
        )

        # School in Other Campus (For Cross-Workspace Isolation Verification)
        self.school_other = School.objects.create(
            workspace=self.ws_other, name="School of Law", code="LAW"
        )

        # Departments
        self.dept_cse = AcademicDepartment.objects.create(school=self.school_eng, name="Computer Science", code="CSE")
        self.dept_ece = AcademicDepartment.objects.create(school=self.school_eng, name="Electronics", code="ECE")
        self.dept_mgt = AcademicDepartment.objects.create(school=self.school_biz, name="Management Studies", code="MGT")

        # Admin Departments
        self.dept_hostel_boys = AdministrativeDepartment.objects.create(
            workspace=self.ws_main, name="Mandela Boys' Hostel", code="BH-1", category="boys_hostel", capacity=300
        )
        self.dept_hostel_girls = AdministrativeDepartment.objects.create(
            workspace=self.ws_main, name="Mother Teresa Girls' Hostel", code="GH-1", category="girls_hostel", capacity=250
        )
        self.dept_it = AdministrativeDepartment.objects.create(
            workspace=self.ws_main, name="Central IT Services", code="IT-01", category="it"
        )
        self.dept_admissions = AdministrativeDepartment.objects.create(
            workspace=self.ws_main, name="Admissions Coordination Office", code="ADM-01", category="admissions"
        )

        # Role Assignments
        RoleAssignment.objects.create(user=self.dean_eng, role="dean", workspace=self.ws_main, school=self.school_eng)
        RoleAssignment.objects.create(user=self.dean_biz, role="dean", workspace=self.ws_main, school=self.school_biz)
        RoleAssignment.objects.create(user=self.reg_user, role="registrar", workspace=self.ws_main)

    def test_cross_workspace_school_isolation(self):
        """School in other workspace must never appear in active workspace querysets."""
        self.client.force_login(self.director)
        session = self.client.session
        session['active_workspace_id'] = self.ws_main.id
        session.save()

        response = self.client.get(reverse('academics:school_list'))
        self.assertEqual(response.status_code, 200)
        schools = list(response.context['schools'])
        self.assertIn(self.school_eng, schools)
        self.assertIn(self.school_biz, schools)
        self.assertNotIn(self.school_other, schools)

    def test_dean_scoped_school_access(self):
        """Dean of Engineering should only see School of Engineering."""
        self.client.force_login(self.dean_eng)
        session = self.client.session
        session['active_workspace_id'] = self.ws_main.id
        session.save()

        filtered_schools = list(CollegeAccessPolicy.filter_schools(self.dean_eng, self.ws_main))
        self.assertIn(self.school_eng, filtered_schools)
        self.assertNotIn(self.school_biz, filtered_schools)
        self.assertNotIn(self.school_other, filtered_schools)

    def test_dean_scoped_department_access(self):
        """Dean of Engineering sees CSE and ECE departments, but not Management (Business)."""
        filtered_depts = list(CollegeAccessPolicy.filter_academic_departments(self.dean_eng, self.ws_main))
        self.assertIn(self.dept_cse, filtered_depts)
        self.assertIn(self.dept_ece, filtered_depts)
        self.assertNotIn(self.dept_mgt, filtered_depts)

    def test_registrar_sees_all_administrative_departments(self):
        """Registrar sees Hostels, IT, and Admissions offices."""
        self.client.force_login(self.reg_user)
        session = self.client.session
        session['active_workspace_id'] = self.ws_main.id
        session.save()

        response = self.client.get(reverse('academics:admin_directory'))
        self.assertEqual(response.status_code, 200)
        depts = list(response.context['departments'])
        self.assertIn(self.dept_hostel_boys, depts)
        self.assertIn(self.dept_hostel_girls, depts)
        self.assertIn(self.dept_it, depts)
        self.assertIn(self.dept_admissions, depts)

    def test_hierarchy_overview_page_renders_cleanly(self):
        """Hierarchy overview page displays leadership, schools, and administrative units."""
        self.client.force_login(self.director)
        session = self.client.session
        session['active_workspace_id'] = self.ws_main.id
        session.save()

        response = self.client.get(reverse('academics:hierarchy_overview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Institutional Hierarchy")
        self.assertContains(response, "School of Engineering")
        self.assertContains(response, "Mandela Boys&#x27; Hostel")
        self.assertContains(response, "Admissions Coordination Office")


class Phase3AcademicManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(name="NexusFlow University Org")
        self.ws_main = Workspace.objects.create(name="Main Campus", slug="main-campus", organization=self.org)
        self.ws_other = Workspace.objects.create(name="Other Campus", slug="other-campus", organization=self.org)

        # Users
        self.director = User.objects.create_user(username="director_user", password="password123", role="director")
        self.prof_smith = User.objects.create_user(username="prof_smith", first_name="John", last_name="Smith", password="password123", role="team_member")
        self.student_cr = User.objects.create_user(username="student_cr", first_name="Alice", last_name="CR", password="password123", role="team_member")
        self.student_other = User.objects.create_user(username="student_other", first_name="Bob", last_name="Student", password="password123", role="team_member")

        # Memberships
        WorkspaceMembership.objects.create(user=self.director, workspace=self.ws_main, role="owner")
        WorkspaceMembership.objects.create(user=self.prof_smith, workspace=self.ws_main, role="team_member")
        WorkspaceMembership.objects.create(user=self.student_cr, workspace=self.ws_main, role="team_member")
        WorkspaceMembership.objects.create(user=self.student_other, workspace=self.ws_main, role="team_member")

        # Academic structure
        self.school_eng = School.objects.create(workspace=self.ws_main, name="School of Engineering", code="ENG")
        self.dept_cse = AcademicDepartment.objects.create(school=self.school_eng, name="Computer Science", code="CSE")
        self.prog_btech = Programme.objects.create(
            department=self.dept_cse, name="B.Tech Computer Science", code="BT-CSE", degree_level="undergraduate"
        )
        self.div_a = ClassDivision.objects.create(
            programme=self.prog_btech, name="Section A", academic_year="2026-2027", semester=5
        )
        self.div_b = ClassDivision.objects.create(
            programme=self.prog_btech, name="Section B", academic_year="2026-2027", semester=5
        )

        # Subject & Faculty
        self.subj_os = Subject.objects.create(department=self.dept_cse, name="Operating Systems", code="CS301", credits=4)
        self.faculty_smith = FacultyProfile.objects.create(
            user=self.prof_smith, employee_id="EMP-001", department=self.dept_cse, designation="Associate Professor"
        )
        self.assignment = TeachingAssignment.objects.create(
            faculty=self.faculty_smith, subject=self.subj_os, division=self.div_a, academic_year="2026-2027"
        )

        # Students
        self.sp_cr = StudentProfile.objects.create(
            user=self.student_cr, student_id="STU-101", programme=self.prog_btech, division=self.div_a, current_semester=5
        )
        self.sp_other = StudentProfile.objects.create(
            user=self.student_other, student_id="STU-102", programme=self.prog_btech, division=self.div_b, current_semester=5
        )

        # CR appointment
        self.cr_role = ClassRepresentative.objects.create(
            student=self.sp_cr, division=self.div_a, is_active=True
        )

    def _set_active_workspace(self, user):
        self.client.force_login(user)
        session = self.client.session
        session['active_workspace_id'] = self.ws_main.id
        session.save()

    def test_programme_and_division_listing(self):
        """Programmes and class divisions list correctly."""
        self._set_active_workspace(self.director)
        resp_prog = self.client.get(reverse('academics:programme_list'))
        self.assertEqual(resp_prog.status_code, 200)
        self.assertContains(resp_prog, "B.Tech Computer Science")

        resp_div = self.client.get(reverse('academics:class_list'))
        self.assertEqual(resp_div.status_code, 200)
        self.assertContains(resp_div, "Section A")
        self.assertContains(resp_div, "Section B")

    def test_programme_coordinator_assignment_kpi_three_of_four_assigned(self):
        """Verify assignment percentage calculation when 3 out of 4 programmes have coordinators (75%)."""
        self._set_active_workspace(self.director)

        # Assign coordinator to initial programme
        self.prog_btech.coordinator = self.prof_smith
        self.prog_btech.save()

        # Create 3 more programmes: 2 with coordinators, 1 unassigned
        prog_ece = Programme.objects.create(
            department=self.dept_cse, name="B.Tech Electronics", code="BT-ECE", degree_level="undergraduate",
            coordinator=self.prof_smith
        )
        prog_mba = Programme.objects.create(
            department=self.dept_cse, name="Executive MBA", code="MBA-EXEC", degree_level="postgraduate",
            coordinator=self.prof_smith
        )
        prog_ba = Programme.objects.create(
            department=self.dept_cse, name="B.A. Digital Media", code="BA-COMM", degree_level="undergraduate",
            coordinator=None
        )

        resp = self.client.get(reverse('academics:programme_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['total_programmes'], 4)
        self.assertEqual(resp.context['assigned_coordinators_count'], 3)
        self.assertEqual(resp.context['assignment_percentage'], 75)
        self.assertContains(resp, "75%")
        self.assertContains(resp, "Assigned")

        # Test dynamic update when coordinator is assigned to the 4th programme
        prog_ba.coordinator = self.prof_smith
        prog_ba.save()

        resp_updated = self.client.get(reverse('academics:programme_list'))
        self.assertEqual(resp_updated.status_code, 200)
        self.assertEqual(resp_updated.context['assigned_coordinators_count'], 4)
        self.assertEqual(resp_updated.context['assignment_percentage'], 100)
        self.assertContains(resp_updated, "100%")

        # Test dynamic update when coordinators are removed
        prog_ba.coordinator = None
        prog_ba.save()
        prog_mba.coordinator = None
        prog_mba.save()

        resp_removed = self.client.get(reverse('academics:programme_list'))
        self.assertEqual(resp_removed.status_code, 200)
        self.assertEqual(resp_removed.context['assigned_coordinators_count'], 2)
        self.assertEqual(resp_removed.context['assignment_percentage'], 50)
        self.assertContains(resp_removed, "50%")

    def test_programme_coordinator_assignment_kpi_zero_programmes_safe(self):
        """Verify no division by zero error occurs when workspace has zero programmes."""
        self._set_active_workspace(self.director)
        Programme.objects.filter(department__school__workspace=self.ws_main).delete()

        resp = self.client.get(reverse('academics:programme_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['total_programmes'], 0)
        self.assertEqual(resp.context['assigned_coordinators_count'], 0)
        self.assertEqual(resp.context['assignment_percentage'], 0)
        self.assertContains(resp, "0%")
        self.assertContains(resp, "Assigned")

    def test_faculty_and_teaching_assignment_views(self):
        """Faculty profiles and teaching allocations render properly."""
        self._set_active_workspace(self.director)
        resp_fac = self.client.get(reverse('academics:faculty_list'))
        self.assertEqual(resp_fac.status_code, 200)
        self.assertContains(resp_fac, "Associate Professor")
        self.assertContains(resp_fac, "EMP-001")

        resp_assign = self.client.get(reverse('academics:teaching_assignments'))
        self.assertEqual(resp_assign.status_code, 200)
        self.assertContains(resp_assign, "Operating Systems")

    def test_cr_portal_access_scoped_to_assigned_division(self):
        """CR user can access their division's CR portal, unauthorized student receives 403."""
        self._set_active_workspace(self.student_cr)
        resp_cr = self.client.get(reverse('academics:cr_portal'))
        self.assertEqual(resp_cr.status_code, 200)
        self.assertContains(resp_cr, "Section A")
        self.assertContains(resp_cr, "STU-101")

        # Non-CR student access denied
        self._set_active_workspace(self.student_other)
        resp_unauth = self.client.get(reverse('academics:cr_portal'))
        self.assertEqual(resp_unauth.status_code, 403)

    def test_cr_roster_view_scoped_to_division(self):
        """CR sees only members of their assigned division in student roster."""
        self._set_active_workspace(self.student_cr)
        resp = self.client.get(reverse('academics:student_roster'))
        self.assertEqual(resp.status_code, 200)
        students = list(resp.context['students'])
        self.assertIn(self.sp_cr, students)
        self.assertNotIn(self.sp_other, students)

    def test_roster_csv_import_success_and_duplicates(self):
        """Administrator can import CSV roster; duplicates are rejected cleanly."""
        self._set_active_workspace(self.director)

        csv_content = (
            "student_id,username,first_name,last_name,email,programme_code,division_name\n"
            "STU-201,carol_w,Carol,White,carol@example.com,BT-CSE,Section A\n"
            "STU-202,david_b,David,Brown,david@example.com,BT-CSE,Section B\n"
        )
        csv_file = SimpleUploadedFile("roster.csv", csv_content.encode("utf-8"), content_type="text/csv")

        resp = self.client.post(reverse('academics:roster_import'), {'roster_file': csv_file})
        self.assertRedirects(resp, reverse('academics:student_roster'))
        self.assertTrue(StudentProfile.objects.filter(student_id="STU-201").exists())
        self.assertTrue(StudentProfile.objects.filter(student_id="STU-202").exists())

        # Attempt duplicate import should fail validation
        csv_file_dup = SimpleUploadedFile("roster_dup.csv", csv_content.encode("utf-8"), content_type="text/csv")
        resp_dup = self.client.post(reverse('academics:roster_import'), {'roster_file': csv_file_dup})
        self.assertEqual(resp_dup.status_code, 200)
        self.assertContains(resp_dup, "Duplicate student ID &#x27;STU-201&#x27;")


class Phase4AdministrativeAndAdmissionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(name="NexusFlow University Org")
        self.ws_main = Workspace.objects.create(name="Main Campus", slug="main-campus", organization=self.org)

        # Users
        self.director = User.objects.create_user(username="director_user", password="password123", role="director")
        self.reg_user = User.objects.create_user(username="registrar_user", password="password123", role="project_manager")
        self.dean_eng = User.objects.create_user(username="dean_eng", password="password123", role="project_manager")
        self.warden = User.objects.create_user(username="warden_user", password="password123", role="team_member")
        self.student = User.objects.create_user(username="student_user", password="password123", role="team_member")

        # Memberships
        WorkspaceMembership.objects.create(user=self.director, workspace=self.ws_main, role="owner")
        WorkspaceMembership.objects.create(user=self.reg_user, workspace=self.ws_main, role="admin")
        WorkspaceMembership.objects.create(user=self.dean_eng, workspace=self.ws_main, role="project_manager")
        WorkspaceMembership.objects.create(user=self.warden, workspace=self.ws_main, role="team_member")
        WorkspaceMembership.objects.create(user=self.student, workspace=self.ws_main, role="team_member")

        # Roles
        RoleAssignment.objects.create(user=self.reg_user, role="registrar", workspace=self.ws_main)
        
        # Schools & Depts
        self.school_eng = School.objects.create(workspace=self.ws_main, name="School of Engineering", code="ENG", dean=self.dean_eng)
        RoleAssignment.objects.create(user=self.dean_eng, role="dean", workspace=self.ws_main, school=self.school_eng)
        self.dept_cse = AcademicDepartment.objects.create(school=self.school_eng, name="Computer Science", code="CSE")
        self.prog_btech = Programme.objects.create(
            department=self.dept_cse, name="B.Tech Computer Science", code="BT-CSE"
        )

        # Hostels & IT
        self.hostel_boys = AdministrativeDepartment.objects.create(
            workspace=self.ws_main,
            name="Mandela Boys' Hostel",
            code="MBH-01",
            category="boys_hostel",
            capacity=320,
            head=self.warden
        )
        RoleAssignment.objects.create(user=self.warden, role="admin_head", workspace=self.ws_main, admin_dept=self.hostel_boys)

        # Project & Task
        self.project_maint = Project.objects.create(title="Campus Facilities & Maintenance", workspace=self.ws_main)
        self.task_hostel = Task.objects.create(
            project=self.project_maint,
            title="Inspect hostel block plumbing and fixtures",
            description="Annual maintenance for Mandela Boys' Hostel",
            status="in_progress"
        )

        # Application
        self.application = AdmissionsApplication.objects.create(
            workspace=self.ws_main,
            application_number="APP-2026-99001",
            first_name="Marcus",
            last_name="Vance",
            email="marcus.vance@example.com",
            phone="+1 555-010-9999",
            targeted_programme=self.prog_btech,
            status="submitted"
        )

    def _login(self, user):
        self.client.force_login(user)
        session = self.client.session
        session['active_workspace_id'] = self.ws_main.id
        session.save()

    def test_hostel_detail_view_renders_capacity_and_tasks(self):
        """Hostel detail displays warden, bed capacity, and linked facilities tasks."""
        self._login(self.director)
        resp = self.client.get(reverse('academics:admin_detail', args=[self.hostel_boys.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Mandela Boys&#x27; Hostel")
        self.assertContains(resp, "320 Beds")
        self.assertContains(resp, "Inspect hostel block plumbing")

    def test_admissions_pipeline_list_and_metrics(self):
        """Admissions list loads pipeline metrics and applications."""
        self._login(self.reg_user)
        resp = self.client.get(reverse('academics:admissions_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "APP-2026-99001")
        self.assertContains(resp, "Marcus Vance")
        self.assertEqual(resp.context['metrics']['submitted'], 1)

    def test_admissions_dual_reporting_workflow(self):
        """
        Dual-reporting verification flow:
        1. Registrar verifies documents and routes to Academic Reviewer.
        2. Dean evaluates academic qualifications and recommends.
        3. Executive issues final formal approval.
        """
        # Step 1: Registrar administrative verification
        self._login(self.reg_user)
        resp_admin = self.client.post(
            reverse('academics:admissions_action', args=[self.application.pk]),
            {
                'action_type': 'admin_verify',
                'decision': 'approved_for_academic',
                'assigned_academic_reviewer': self.dean_eng.id,
                'comments': 'Transcripts and identity documents verified. Ready for Dean evaluation.'
            }
        )
        self.assertRedirects(resp_admin, reverse('academics:admissions_detail', args=[self.application.pk]))
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'academic_review')
        self.assertEqual(self.application.assigned_academic_reviewer, self.dean_eng)
        self.assertEqual(self.application.reviews.count(), 1)
        self.assertEqual(self.application.reviews.first().stage, 'admin')

        # Step 2: Dean academic evaluation
        self._login(self.dean_eng)
        resp_acad = self.client.post(
            reverse('academics:admissions_action', args=[self.application.pk]),
            {
                'action_type': 'academic_review',
                'decision': 'recommended',
                'comments': 'Strong background in Mathematics and Computing. Recommended for B.Tech CSE.'
            }
        )
        self.assertRedirects(resp_acad, reverse('academics:admissions_detail', args=[self.application.pk]))
        self.assertEqual(self.application.reviews.count(), 2)
        latest_rev = self.application.reviews.order_by('-created_at').first()
        self.assertEqual(latest_rev.stage, 'academic')
        self.assertEqual(latest_rev.decision, 'recommended')

        # Step 3: Executive final decision
        self._login(self.director)
        resp_final = self.client.post(
            reverse('academics:admissions_action', args=[self.application.pk]),
            {
                'action_type': 'finalize',
                'final_decision': 'approved',
                'comments': 'Formal admission approved with Presidential scholarship.'
            }
        )
        self.assertRedirects(resp_final, reverse('academics:admissions_detail', args=[self.application.pk]))
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'approved')
        self.assertEqual(self.application.reviews.count(), 3)



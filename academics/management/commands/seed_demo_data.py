from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core.models import User, Organization, Workspace, WorkspaceMembership
from projects.models import Project
from tasks.models import Task
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

class Command(BaseCommand):
    help = "Seeds comprehensive, high-fidelity synthetic demo data for Aurevia University Academic Operations."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing Aurevia University Academic Operations demo seed..."))

        # 1. Organization & Campus Workspace
        org, _ = Organization.objects.get_or_create(name="Aurevia Higher Education System")
        
        # Check if legacy workspace exists to update smoothly without duplicating
        workspace = Workspace.objects.filter(slug__in=["aurevia-main", "nexusflow-main"]).first()
        if workspace:
            workspace.name = "Aurevia University — Main Campus"
            workspace.slug = "aurevia-main"
            workspace.organization = org
            workspace.save()
        else:
            workspace = Workspace.objects.create(
                slug="aurevia-main",
                name="Aurevia University — Main Campus",
                organization=org
            )
        self.stdout.write(self.style.SUCCESS(f"Workspace: {workspace.name}"))

        # Helper to create/get/update users
        def create_user(username, email, first_name, last_name, role='team_member', is_staff=False):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': role,
                    'is_staff': is_staff,
                }
            )
            # Ensure email, name, role and demo password are aligned
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.role = role
            user.is_staff = is_staff
            user.set_password("Aurevia2026!")
            user.save()

            WorkspaceMembership.objects.get_or_create(
                user=user,
                workspace=workspace,
                defaults={'role': 'owner' if role == 'director' else ('admin' if role == 'project_manager' else 'team_member')}
            )
            return user

        # 2. Institutional Leadership
        pres_user = create_user("president_vance", "president@aurevia.edu", "Dr. Eleanor", "Vance", role="director", is_staff=True)
        prov_user = create_user("provost_pendelton", "provost@aurevia.edu", "Dr. Arthur", "Pendelton", role="director", is_staff=True)
        reg_user = create_user("registrar_hayes", "registrar@aurevia.edu", "Dr. Margaret", "Hayes", role="project_manager", is_staff=True)

        RoleAssignment.objects.get_or_create(user=pres_user, workspace=workspace, role="president")
        RoleAssignment.objects.get_or_create(user=prov_user, workspace=workspace, role="provost")
        RoleAssignment.objects.get_or_create(user=reg_user, workspace=workspace, role="registrar")

        # 3. Deans & Schools
        dean_eng_u = create_user("dean_chen", "dean.eng@aurevia.edu", "Dr. Robert", "Chen", role="project_manager")
        dean_biz_u = create_user("dean_sterling", "dean.biz@aurevia.edu", "Dr. Sophia", "Sterling", role="project_manager")
        dean_hss_u = create_user("dean_aurelius", "dean.hss@aurevia.edu", "Dr. Marcus", "Aurelius", role="project_manager")

        school_eng, _ = School.objects.get_or_create(
            workspace=workspace, code="ENG",
            defaults={"name": "School of Engineering & Technology", "dean": dean_eng_u, "description": "Cutting-edge computing, electronics, and applied engineering."}
        )
        school_biz, _ = School.objects.get_or_create(
            workspace=workspace, code="BIZ",
            defaults={"name": "School of Business & Management", "dean": dean_biz_u, "description": "Global enterprise, analytics, finance, and strategic leadership."}
        )
        school_hss, _ = School.objects.get_or_create(
            workspace=workspace, code="HSS",
            defaults={"name": "School of Humanities & Social Sciences", "dean": dean_hss_u, "description": "Media, psychological sciences, communication, and humanities."}
        )

        RoleAssignment.objects.get_or_create(user=dean_eng_u, workspace=workspace, school=school_eng, role="dean")
        RoleAssignment.objects.get_or_create(user=dean_biz_u, workspace=workspace, school=school_biz, role="dean")
        RoleAssignment.objects.get_or_create(user=dean_hss_u, workspace=workspace, school=school_hss, role="dean")

        # 4. Academic Departments & HoDs
        hod_cse_u = create_user("hod_cse", "hod.cse@aurevia.edu", "Dr. Vikram", "Deshmukh", role="project_manager")
        hod_ece_u = create_user("hod_ece", "hod.ece@aurevia.edu", "Dr. Ananya", "Sen", role="project_manager")
        hod_mgt_u = create_user("hod_mgt", "hod.mgt@aurevia.edu", "Dr. David", "Kim", role="project_manager")

        dept_cse, _ = AcademicDepartment.objects.get_or_create(school=school_eng, code="CSE", defaults={"name": "Computer Science & Engineering", "hod": hod_cse_u})
        dept_ece, _ = AcademicDepartment.objects.get_or_create(school=school_eng, code="ECE", defaults={"name": "Electrical & Electronics Engineering", "hod": hod_ece_u})
        dept_mech, _ = AcademicDepartment.objects.get_or_create(school=school_eng, code="MECH", defaults={"name": "Mechanical & Aerospace Engineering"})
        dept_mgt, _ = AcademicDepartment.objects.get_or_create(school=school_biz, code="MGT", defaults={"name": "Management Studies & Strategy", "hod": hod_mgt_u})
        dept_fin, _ = AcademicDepartment.objects.get_or_create(school=school_biz, code="FIN", defaults={"name": "Finance & Quantitative Economics"})
        dept_comm, _ = AcademicDepartment.objects.get_or_create(school=school_hss, code="COMM", defaults={"name": "Media & Digital Communications"})

        RoleAssignment.objects.get_or_create(user=hod_cse_u, workspace=workspace, academic_dept=dept_cse, role="hod")
        RoleAssignment.objects.get_or_create(user=hod_ece_u, workspace=workspace, academic_dept=dept_ece, role="hod")
        RoleAssignment.objects.get_or_create(user=hod_mgt_u, workspace=workspace, academic_dept=dept_mgt, role="hod")

        # 5. Degree Programmes & Class Divisions
        prog_cse, _ = Programme.objects.get_or_create(
            department=dept_cse, code="BT-CSE",
            defaults={"name": "B.Tech Computer Science & Engineering", "degree_level": "undergraduate", "duration_years": 4, "total_semesters": 8, "coordinator": hod_cse_u}
        )
        prog_ece, _ = Programme.objects.get_or_create(
            department=dept_ece, code="BT-ECE",
            defaults={"name": "B.Tech Electrical & Electronics Engineering", "degree_level": "undergraduate", "duration_years": 4, "total_semesters": 8, "coordinator": hod_ece_u}
        )
        prog_mba, _ = Programme.objects.get_or_create(
            department=dept_mgt, code="MBA-EXEC",
            defaults={"name": "Executive Master of Business Administration", "degree_level": "postgraduate", "duration_years": 2, "total_semesters": 4, "coordinator": hod_mgt_u}
        )
        prog_comm, _ = Programme.objects.get_or_create(
            department=dept_comm, code="BA-COMM",
            defaults={"name": "B.A. Digital Media & Journalism", "degree_level": "undergraduate", "duration_years": 3, "total_semesters": 6}
        )

        div_cse_5a, _ = ClassDivision.objects.get_or_create(programme=prog_cse, academic_year="2026-2027", semester=5, name="Section A")
        div_cse_5b, _ = ClassDivision.objects.get_or_create(programme=prog_cse, academic_year="2026-2027", semester=5, name="Section B")
        div_ece_3a, _ = ClassDivision.objects.get_or_create(programme=prog_ece, academic_year="2026-2027", semester=3, name="Section A")
        div_mba_1a, _ = ClassDivision.objects.get_or_create(programme=prog_mba, academic_year="2026-2027", semester=1, name="Section A")

        # 6. Faculty, Subjects & Allocations
        turing_u = create_user("prof_turing", "alan.turing@aurevia.edu", "Alan", "Turing", role="team_member")
        shannon_u = create_user("prof_shannon", "claude.shannon@aurevia.edu", "Claude", "Shannon", role="team_member")
        lovelace_u = create_user("dr_lovelace", "ada.lovelace@aurevia.edu", "Ada", "Lovelace", role="team_member")
        kotler_u = create_user("prof_kotler", "philip.kotler@aurevia.edu", "Philip", "Kotler", role="team_member")

        fac_turing, _ = FacultyProfile.objects.get_or_create(user=turing_u, defaults={"employee_id": "FAC-001", "department": dept_cse, "designation": "Associate Professor", "office_location": "Turing Hall 302"})
        fac_shannon, _ = FacultyProfile.objects.get_or_create(user=shannon_u, defaults={"employee_id": "FAC-002", "department": dept_ece, "designation": "Professor", "office_location": "Maxwell Lab 105"})
        fac_lovelace, _ = FacultyProfile.objects.get_or_create(user=lovelace_u, defaults={"employee_id": "FAC-003", "department": dept_cse, "designation": "Assistant Professor", "office_location": "Turing Hall 204"})
        fac_kotler, _ = FacultyProfile.objects.get_or_create(user=kotler_u, defaults={"employee_id": "FAC-004", "department": dept_mgt, "designation": "Professor & Chair", "office_location": "Drucker Tower 410"})

        subj_os, _ = Subject.objects.get_or_create(department=dept_cse, code="CS501", defaults={"name": "Operating Systems & Concurrency", "credits": 4, "semester_recommended": 5})
        subj_db, _ = Subject.objects.get_or_create(department=dept_cse, code="CS502", defaults={"name": "Database Management Systems & SQL", "credits": 4, "semester_recommended": 5})
        subj_sig, _ = Subject.objects.get_or_create(department=dept_ece, code="EC301", defaults={"name": "Signals & Linear Systems", "credits": 3, "semester_recommended": 3})
        subj_strat, _ = Subject.objects.get_or_create(department=dept_mgt, code="MG101", defaults={"name": "Corporate Strategy & Leadership", "credits": 3, "semester_recommended": 1})

        TeachingAssignment.objects.get_or_create(faculty=fac_turing, subject=subj_os, division=div_cse_5a, academic_year="2026-2027", defaults={"schedule_details": "Mon/Wed/Fri 10:00 - 11:30 AM"})
        TeachingAssignment.objects.get_or_create(faculty=fac_lovelace, subject=subj_db, division=div_cse_5a, academic_year="2026-2027", defaults={"schedule_details": "Tue/Thu 02:00 - 04:00 PM"})
        TeachingAssignment.objects.get_or_create(faculty=fac_shannon, subject=subj_sig, division=div_ece_3a, academic_year="2026-2027", defaults={"schedule_details": "Mon/Wed 09:00 - 10:30 AM"})
        TeachingAssignment.objects.get_or_create(faculty=fac_kotler, subject=subj_strat, division=div_mba_1a, academic_year="2026-2027", defaults={"schedule_details": "Sat 09:00 AM - 01:00 PM"})

        # 7. Students & Class Representatives
        stu_data = [
            ("student_alice", "alice.zhang@aurevia.edu", "Alice", "Zhang", "STU-2026-001", prog_cse, div_cse_5a, 5, True),
            ("student_bob", "bob.martin@aurevia.edu", "Bob", "Martin", "STU-2026-002", prog_cse, div_cse_5a, 5, False),
            ("student_charlie", "charlie.davis@aurevia.edu", "Charlie", "Davis", "STU-2026-003", prog_cse, div_cse_5b, 5, False),
            ("student_diana", "diana.prince@aurevia.edu", "Diana", "Prince", "STU-2026-004", prog_ece, div_ece_3a, 3, True),
            ("student_evan", "evan.wright@aurevia.edu", "Evan", "Wright", "STU-2026-005", prog_mba, div_mba_1a, 1, False),
            ("student_fiona", "fiona.gallagher@aurevia.edu", "Fiona", "Gallagher", "STU-2026-006", prog_comm, None, 1, False),
        ]

        for uname, uemail, fname, lname, sid, prog, div, sem, is_cr in stu_data:
            s_u = create_user(uname, uemail, fname, lname, role="team_member")
            sp, _ = StudentProfile.objects.get_or_create(
                student_id=sid,
                defaults={"user": s_u, "programme": prog, "division": div, "current_semester": sem, "enrollment_status": "active"}
            )
            if is_cr and div:
                ClassRepresentative.objects.get_or_create(student=sp, division=div, defaults={"is_active": True})
                RoleAssignment.objects.get_or_create(user=s_u, workspace=workspace, division=div, role="cr")

        # 8. Administrative Departments (Hostels, IT, Admissions)
        warden_b_u = create_user("warden_mens", "warden.boys@aurevia.edu", "Col. James", "Rhodes", role="team_member")
        warden_g_u = create_user("warden_womens", "warden.girls@aurevia.edu", "Dr. Beverly", "Crusher", role="team_member")
        it_head_u = create_user("it_director", "it.head@aurevia.edu", "Geordi", "LaForge", role="project_manager")
        adm_lead_u = create_user("admissions_officer", "admissions.officer@aurevia.edu", "Nyota", "Uhura", role="project_manager")
        fin_lead_u = create_user("bursar_finance", "bursar@aurevia.edu", "Montgomery", "Scott", role="project_manager")

        hostel_boys, _ = AdministrativeDepartment.objects.get_or_create(
            workspace=workspace, code="MBH-01",
            defaults={"name": "Nelson Mandela Boys' Residence Hall", "category": "boys_hostel", "head": warden_b_u, "capacity": 320, "contact_phone": "+1 555-019-1001"}
        )
        hostel_girls, _ = AdministrativeDepartment.objects.get_or_create(
            workspace=workspace, code="MTGH-01",
            defaults={"name": "Mother Teresa Women's Residence Hall", "category": "girls_hostel", "head": warden_g_u, "capacity": 280, "contact_phone": "+1 555-019-1002"}
        )
        it_dept, _ = AdministrativeDepartment.objects.get_or_create(
            workspace=workspace, code="IT-01",
            defaults={"name": "Campus IT Systems & Network Operations", "category": "it", "head": it_head_u, "contact_email": "servicedesk@aurevia.edu"}
        )
        adm_dept, _ = AdministrativeDepartment.objects.get_or_create(
            workspace=workspace, code="ADM-01",
            defaults={"name": "Admissions Coordination Office", "category": "admissions", "head": adm_lead_u, "contact_email": "admissions@aurevia.edu"}
        )
        fin_dept, _ = AdministrativeDepartment.objects.get_or_create(
            workspace=workspace, code="FIN-01",
            defaults={"name": "Bursar & Student Financial Services", "category": "finance", "head": fin_lead_u, "contact_email": "bursar@aurevia.edu"}
        )

        RoleAssignment.objects.get_or_create(user=warden_b_u, workspace=workspace, admin_dept=hostel_boys, role="admin_head")
        RoleAssignment.objects.get_or_create(user=warden_g_u, workspace=workspace, admin_dept=hostel_girls, role="admin_head")
        RoleAssignment.objects.get_or_create(user=it_head_u, workspace=workspace, admin_dept=it_dept, role="admin_head")
        RoleAssignment.objects.get_or_create(user=adm_lead_u, workspace=workspace, admin_dept=adm_dept, role="admissions_officer")
        RoleAssignment.objects.get_or_create(user=fin_lead_u, workspace=workspace, admin_dept=fin_dept, role="admin_head")

        # 9. Campus Projects & Maintenance Tasks
        proj_fac, _ = Project.objects.get_or_create(
            title="Campus Facilities & Maintenance 2026-27",
            workspace=workspace,
            defaults={"status": "active", "manager": reg_user, "description": "Routine and emergency maintenance for dormitories and campus academic blocks."}
        )
        Task.objects.get_or_create(
            project=proj_fac, title="Inspect plumbing & fixture valves in Mandela Boys' Hostel",
            defaults={"assignee": warden_b_u, "status": "in_progress", "priority": "high", "description": "Annual pre-winter inspection of boiler systems and dorm fixtures."}
        )
        Task.objects.get_or_create(
            project=proj_fac, title="Repair study hall HVAC air handlers in Mother Teresa Hall",
            defaults={"assignee": warden_g_u, "status": "todo", "priority": "medium"}
        )

        proj_it, _ = Project.objects.get_or_create(
            title="Campus Digital Infrastructure Upgrade",
            workspace=workspace,
            defaults={"status": "active", "manager": it_head_u, "description": "Core switch renewal, WiFi 6 AP distribution, and student lab modernization."}
        )
        Task.objects.get_or_create(
            project=proj_it, title="Firmware patch rollout for core distribution routers",
            defaults={"assignee": it_head_u, "status": "done", "priority": "high"}
        )
        Task.objects.get_or_create(
            project=proj_it, title="Deploy 48 high-density WiFi 6 APs in Engineering Lecture Halls",
            defaults={"assignee": it_head_u, "status": "in_progress", "priority": "medium"}
        )

        # 10. Admissions Pipeline & Dual-Reporting Workflow Entries
        # Candidate 1: In Academic Review
        app1, _ = AdmissionsApplication.objects.get_or_create(
            application_number="APP-2026-1001",
            workspace=workspace,
            defaults={
                "first_name": "Liam",
                "last_name": "Gallagher",
                "email": "liam.gallagher@example.com",
                "phone": "+1 555-012-3401",
                "targeted_programme": prog_cse,
                "status": "academic_review",
                "assigned_admin": adm_lead_u,
                "assigned_academic_reviewer": dean_eng_u
            }
        )
        AdmissionsReview.objects.get_or_create(
            application=app1,
            stage="admin",
            defaults={
                "reviewer": adm_lead_u,
                "decision": "recommended",
                "comments": "High school transcript, math scores (top 5%), and ID verified. Routed to Dean Chen for faculty review."
            }
        )

        # Candidate 2: Formally Approved
        app2, _ = AdmissionsApplication.objects.get_or_create(
            application_number="APP-2026-1002",
            workspace=workspace,
            defaults={
                "first_name": "Sophia",
                "last_name": "Patel",
                "email": "sophia.patel@example.com",
                "phone": "+1 555-012-3402",
                "targeted_programme": prog_cse,
                "status": "approved",
                "assigned_admin": adm_lead_u,
                "assigned_academic_reviewer": dean_eng_u
            }
        )
        AdmissionsReview.objects.get_or_create(
            application=app2,
            stage="admin",
            defaults={
                "reviewer": adm_lead_u,
                "decision": "recommended",
                "comments": "All entrance requirements satisfied. Fast-tracked for honors review."
            }
        )
        AdmissionsReview.objects.get_or_create(
            application=app2,
            stage="academic",
            decision="recommended",
            defaults={
                "reviewer": dean_eng_u,
                "comments": "Exemplary code portfolio and mathematics competition record. Strongly recommended."
            }
        )
        AdmissionsReview.objects.get_or_create(
            application=app2,
            stage="academic",
            decision="approved",
            defaults={
                "reviewer": prov_user,
                "comments": "Formally approved for B.Tech Computer Science Class of 2030 with University Merit Scholarship."
            }
        )

        # Candidate 3: Admin Review
        app3, _ = AdmissionsApplication.objects.get_or_create(
            application_number="APP-2026-1003",
            workspace=workspace,
            defaults={
                "first_name": "James",
                "last_name": "O'Connor",
                "email": "james.oconnor@example.com",
                "phone": "+1 555-012-3403",
                "targeted_programme": prog_mba,
                "status": "admin_review",
                "assigned_admin": adm_lead_u,
            }
        )
        AdmissionsReview.objects.get_or_create(
            application=app3,
            stage="admin",
            defaults={
                "reviewer": adm_lead_u,
                "decision": "info_required",
                "comments": "Requested official undergraduate degree completion certificate from prior university."
            }
        )

        # Candidate 4: New Submission
        app4, _ = AdmissionsApplication.objects.get_or_create(
            application_number="APP-2026-1004",
            workspace=workspace,
            defaults={
                "first_name": "Elena",
                "last_name": "Rostova",
                "email": "elena.rostova@example.com",
                "phone": "+1 555-012-3404",
                "targeted_programme": prog_comm,
                "status": "submitted"
            }
        )

        self.stdout.write(self.style.SUCCESS("Synthetic demo data seeding completed successfully!"))

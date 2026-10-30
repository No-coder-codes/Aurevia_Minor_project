# Aurevia — Evaluator Guide and Demonstration Script

**Project:** Aurevia Higher-Education Operations & Academic Management SaaS  
**Codebase:** `D:\Django\Project`  
**Framework:** Django 6.0, Python 3.13, Bootstrap 5, SQLite  
**Design System:** Aurevia Enterprise SaaS Design System (Dark Navy / Indigo-Violet)  

---

## 1. Project Overview & Problem Statement

Modern higher-education institutions face fragmented administrative software: academic hierarchies (schools, departments, degrees), operational facilities (hostels, maintenance, IT tickets), cross-functional admissions evaluations, and student governance typically exist in isolated silos. 

**Aurevia** is a multi-tenant, unified Higher-Education Operations Platform providing:
- **Hierarchical Governance:** Multi-tier academic trees (Chancellor $\rightarrow$ Provost $\rightarrow$ Deans $\rightarrow$ HoDs $\rightarrow$ Faculty $\rightarrow$ Students) aligned with administrative operations (Registrar $\rightarrow$ Wardens, Facilities, Bursar).
- **Dual-Reporting Workflows:** Admissions review pipelines where administrative credential validation and faculty academic merit appraisals are tracked concurrently with immutable audit logs.
- **Tenant Security & Isolation:** Strict workspace-scoping across models, views, file exports, and API endpoints, preventing unauthorized cross-campus data leakage.
- **Representative Student Governance:** Dedicated Class Representative (CR) portals providing section management while enforcing strict privilege boundaries.

---

## 2. Intended Users & Role Hierarchy

| Role Persona | Synthetic Demo Account | System Role | Primary Responsibilities |
| :--- | :--- | :--- | :--- |
| **President / Chancellor** | `president_vance` | `director` (Owner) | Executive institutional oversight, campus-wide KPIs, cross-school operations |
| **Provost / Academic VP** | `provost_pendelton` | `director` | Academic governance, curriculum oversight, final admissions authorization |
| **Dean of Engineering** | `dean_chen` | `project_manager` (Admin) | School of Engineering leadership, faculty allocations, admissions evaluations |
| **Admissions Officer** | `admissions_officer` | `project_manager` | Dual-reporting intake queue, candidate document verification |
| **Hostel Warden / Facilities** | `warden_mens` | `team_member` | Residence hall facilities, infrastructure work orders, maintenance tasks |
| **Faculty Member** | `prof_turing` | `team_member` | Teaching assignments, course syllabus management, student supervision |
| **Class Representative (CR)** | `student_alice` | `team_member` (Student/CR) | Section class roster view, instructor communications, student concerns |

> [!NOTE]  
> All demo credentials listed above are strictly **synthetic test accounts** created for evaluation. The standardized evaluation password across all seeded demo accounts is: `Aurevia2026!`

---

## 3. Quick Startup & Access Instructions

### Step 1: Start the Development Server
Open PowerShell in `D:\Django\Project` and run:
```powershell
.\venv\Scripts\python.exe manage.py runserver
```

### Step 2: Access the Application
Open your web browser and navigate to:
```text
http://127.0.0.1:8000/
```
If you are unauthenticated, you will automatically be directed to `http://127.0.0.1:8000/login/`.

### Step 3: One-Click Demo Login
On the login screen, click any of the **Quick Demo Personas** buttons (e.g. *President Vance*, *Dean Chen*, *Admissions Officer*, or *Student Alice*) to populate credentials automatically with `Aurevia2026!`, then click **Sign In to Campus**.

---

## 4. Five-Minute Live Demonstration Script

| Timing | Demonstration Step | Target Screen & URL | Actions & Talking Points |
| :---: | :--- | :--- | :--- |
| **0:00 – 0:45** | **Brand & One-Click Authentication** | `/login/` | • Highlight Aurevia University branding and SVG emblem.<br>• Toggle Dark/Light mode theme switch to show instant palette adaptation.<br>• Click the **President Vance** persona button to auto-fill synthetic credentials.<br>• Click **Sign In to Campus**. |
| **0:45 – 1:45** | **Executive Campus Dashboard & Risk Analysis** | `/` | • Point out campus KPI cards: Schools (3), Programmes (4), Enrolled Students, Infrastructure Projects.<br>• Review the **Campus Operations & Infrastructure Projects** table.<br>• Explain the automated **Risk Analysis engine** (`On Track`, `At Risk`, `Off Track`) and timeline countdowns.<br>• Highlight the live Campus Audit Trail at the bottom of the dashboard. |
| **1:45 – 2:45** | **Institutional Governance & Academic Tree** | `/college/hierarchy/`<br>`/college/schools/` | • Open **Institutional Hierarchy** to demonstrate the dual-tier organizational model: Provost's Academic branch vs. Registrar's Operations branch.<br>• Navigate to **Schools Directory** (`/college/schools/`) and drill into the School of Engineering (`/college/schools/1/`).<br>• Show constituent departments (CSE, ECE, MECH) and accredited degree programmes (`/college/programmes/`).<br>• Show **Administrative Directory** (`/college/admin-directory/`) featuring Mandela Boys' Hall and Mother Teresa Women's Hall. |
| **2:45 – 3:30** | **Admissions Dual-Reporting Pipeline** | `/college/admissions/` | • Open Admissions Management to view the cross-functional pipeline (Total, Admin Review, Academic Review, Approved).<br>• Click applicant **Liam Gallagher** (`/college/admissions/1/`) or **Sophia Patel** (`/college/admissions/2/`).<br>• Walk through the dual-stage audit trail: Stage 1 (Administrative verification by Officer Uhura) $\rightarrow$ Stage 2 (Academic evaluation by Dean Chen). |
| **3:30 – 4:15** | **Student Roster & Atomic Batch Import** | `/college/students/`<br>`/college/students/import/` | • Review the live Student Roster; demonstrate real-time filtering by Degree Programme (CSE) and Class Section.<br>• Click **Import CSV/Excel** (`/college/students/import/`).<br>• Point out the evaluator helper banner referencing the pre-validated demo sample at `docs/demo/demo_roster_sample.csv` (10 verified records mapped cleanly to active programmes). |
| **4:15 – 5:00** | **Class Representative (CR) Experience** | `/logout/` $\rightarrow$ `/login/` $\rightarrow$ `/college/cr-portal/` | • Log out and click **Student Alice** (`student_alice` / `Aurevia2026!`).<br>• Show the **Student & Representative Workspace Banner** on the dashboard displaying Alice's student ID (`STU-2026-001`) and direct portal link.<br>• Open **CR Portal** (`/college/cr-portal/`): show Section A roster access and instructor contact tools.<br>• Note the security boundary: administrative operations and billing changes are locked from student roles. |

---

## 5. Route & Feature Demonstration Matrix

| Route Path | Module / Feature | Verified Capabilities | Evaluator Focus |
| :--- | :--- | :--- | :--- |
| `/login/` | Authentication | Synthetic 1-click persona fill, show/hide password, theme switch | Usability & ease of evaluation |
| `/` | Executive Dashboard | Campus KPIs, risk intelligence status, timeline trackers, recent audit logs | Executive decision support |
| `/college/hierarchy/` | Institutional Hierarchy | Dual-branch academic vs. administrative governance tree | Structural modeling & architecture |
| `/college/schools/` | Schools Directory | Constituent faculties, assigned Deans, departments count | Academic organizational structure |
| `/college/programmes/` | Degree Programmes | Undergraduate & postgraduate degree curricula | Degree tracking |
| `/college/classes/` | Class Sections | Academic year, semester, and section divisions | Cohort management |
| `/college/faculty/` | Faculty Roster | Academic profiles, designations, office locations | Staff directory |
| `/college/teaching-assignments/`| Faculty Allocations | Faculty-to-subject-to-section teaching schedules | Workload allocation |
| `/college/students/` | Student Rosters | Enrolled student listings with dynamic programme/division filters | Student record management |
| `/college/students/import/` | Bulk Roster Import | Atomic multi-row CSV/XLSX validation with row-level error reporting | Data ingestion robustness |
| `/college/cr-portal/` | CR Student Portal | Division roster access, instructor coordination for elected CRs | Student representative governance |
| `/college/admissions/` | Admissions Pipeline | Dual-reporting stages (Admin verification + Academic review) | Cross-functional workflows |
| `/college/admin-directory/` | Hostels & Facilities | Dormitories, IT network operations, bursar financial office | Non-academic campus operations |
| `/tasks/` | Operations Tasks | List and Kanban views, priority filters, assignment tracking | Operations execution |
| `/files/` | Document Library | Project-scoped file management with upload modal | Institutional compliance records |
| `/history/` | Audit Trail | System-wide timestamped activity log with user attribution | Accountability & security audit |

---

## 6. Automated Test Suites & Rerun Commands

The application is backed by an automated test suite verifying tenant security, workspace isolation, admissions state transitions, and academic workflows.

### Run All Test Suites
```powershell
.\venv\Scripts\python.exe manage.py test core.tests documents.tests academics.tests
```
**Expected Outcome:** 60 tests passing, 0 failures, 0 errors (`Ran 60 tests in ~220s - OK`).

### Run Django System Integrity Check
```powershell
.\venv\Scripts\python.exe manage.py check
```
**Expected Outcome:** `System check identified no issues (0 silenced).`

### Re-seed Synthetic Demo Data (If Reset is Required)
```powershell
.\venv\Scripts\python.exe manage.py seed_demo_data
```
**Expected Outcome:** Resets and aligns all synthetic users, schools, admissions records, and demo rosters without duplicating records.

---

## 7. Verification Classification & Current Limitations

### A. Verified at Runtime (Independently Confirmed)
- **Authentication & Personas:** All 4 primary demo personas (`president_vance`, `dean_chen`, `admissions_officer`, `student_alice`) authenticate successfully with `Aurevia2026!`.
- **Route Status Codes:** All 16 primary routes return HTTP 200 for authorized personas.
- **Role Permission Enforcement:** `/college/cr-portal/` returns HTTP 200 for `student_alice` and correctly blocks unauthorized non-CR accounts with HTTP 403 Forbidden.
- **Roster Ingestion Schema:** Verified that `docs/demo/demo_roster_sample.csv` matches the 7 required columns (`student_id`, `username`, `first_name`, `last_name`, `email`, `programme_code`, `division_name`) and adheres to unique database constraints.
- **Automated Test Coverage:** 60/60 tests passing cleanly under `manage.py test`.

### B. Verified in Source Code (Static Inspection)
- **Tenant Isolation:** Workspace scoping in view querysets (`WorkspaceIsolatedMixin`), preventing cross-campus data leakage.
- **Atomic Transactions:** Database mutations in bulk student CSV imports wrapped in `transaction.atomic()` to guarantee all-or-nothing execution.
- **Dark/Light Mode Tokens:** Pure CSS variables with zero FOUC script in `templates/base.html`.

### C. Unverified / Intentional Prototype Boundaries
1. **Live External SMTP:** System notifications are stored in the database and audit trail; real-world external email delivery via third-party SMTP servers is not configured for offline evaluation.
2. **Cloud Object Storage:** File uploads are stored on local filesystem media storage (`MEDIA_ROOT`), not external S3/GCS buckets.
3. **Subdomain Multi-Tenancy:** The application isolates campuses via workspace database keys and session context, rather than dynamic DNS wildcard subdomains (`campus.aurevia.edu`).

---

*This guide serves as the official walkthrough script for academic examination and technical defense of the Aurevia platform.*

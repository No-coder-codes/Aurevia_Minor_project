# Aurevia — Task 2: Academic Demo Assets Finalisation Report

**Project Path:** `D:\Django\Project`  
**Execution Status:** Completed & 100% Verified  
**Report Artifact:** `AUREVIA_TASK2_REPORT.md`  

---

## 1. Summary of Actions Completed

Task 2 focused on preparing verified demonstration assets and assessing demo data completeness for academic evaluation:
1. **Identified Exact Importer Specification**: Inspected `academics/views.py:StudentRosterImportView` to extract exact required CSV column headers, encoding expectations (`utf-8-sig` / `utf-8`), data validation rules, and division mapping logic.
2. **Created Sample Demo Roster CSV**: Created `docs/demo/demo_roster_sample.csv` populated with 10 realistic, internally consistent student records matching seeded degree programmes and class divisions.
3. **Assessed Existing Seed Data**: Inspected `seed_demo_data.py` and the live database. Confirmed that the current dataset provides complete, multi-tiered coverage across Schools, Departments, Degree Programmes, Class Divisions, Faculty Teaching Allocations, Admissions Pipeline, and Campus Operations. Per the scope mandate (*"If the dataset is sufficient, do not add more records"*), no redundant database records were injected.
4. **Isolated End-to-End Import Verification**: Verified 100% schema compatibility by testing parsing and atomic HTTP POST import against `StudentRosterImportView` in an isolated rollback transaction, ensuring live database records remain untouched.

---

## 2. Files Created or Modified

| File | Status | Description |
| :--- | :--- | :--- |
| `docs/demo/demo_roster_sample.csv` | **Created** | Fictional student dataset (10 records) ready for demonstration on `/college/students/import/`. |
| `AUREVIA_TASK2_REPORT.md` | **Created** | Formal Task 2 completion report in project root. |

*No application code, migrations, database tables, or configuration files were modified.*

---

## 3. Sample CSV Specification & Record Inventory

### A. Column Headers Required by Importer
The importer in `StudentRosterImportView` accepts the following exact CSV headers:
```csv
student_id,username,first_name,last_name,email,programme_code,division_name
```

- `student_id` *(Required)*: Unique student identifier (e.g., `STU-2026-101`).
- `username` *(Required)*: Unique alphanumeric user handle (e.g., `liam_patel`).
- `first_name` *(Optional but recommended)*: Student given name.
- `last_name` *(Optional but recommended)*: Student surname.
- `email` *(Required)*: Institutional contact email (`@aurevia.edu`).
- `programme_code` *(Required)*: Case-insensitive match against active campus degree programme (`BT-CSE`, `BT-ECE`, `MBA-EXEC`, `BA-COMM`).
- `division_name` *(Optional)*: Matched against active division in programme (`Section A`, `Section B`, or empty for unassigned).

### B. Record Inventory (`docs/demo/demo_roster_sample.csv`)

| Row | Student ID | Username | Name | Email | Programme | Division |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| 1 | `STU-2026-101` | `liam_patel` | Liam Patel | `liam.patel@aurevia.edu` | `BT-CSE` | Section A |
| 2 | `STU-2026-102` | `sophia_kim` | Sophia Kim | `sophia.kim@aurevia.edu` | `BT-CSE` | Section A |
| 3 | `STU-2026-103` | `noah_garcia` | Noah Garcia | `noah.garcia@aurevia.edu` | `BT-CSE` | Section B |
| 4 | `STU-2026-104` | `emma_johnson` | Emma Johnson | `emma.johnson@aurevia.edu` | `BT-CSE` | Section B |
| 5 | `STU-2026-105` | `aarav_sharma` | Aarav Sharma | `aarav.sharma@aurevia.edu` | `BT-ECE` | Section A |
| 6 | `STU-2026-106` | `olivia_brown` | Olivia Brown | `olivia.brown@aurevia.edu` | `BT-ECE` | Section A |
| 7 | `STU-2026-107` | `lucas_muller` | Lucas Muller | `lucas.muller@aurevia.edu` | `MBA-EXEC` | Section A |
| 8 | `STU-2026-108` | `mia_tanaka` | Mia Tanaka | `mia.tanaka@aurevia.edu` | `MBA-EXEC` | Section A |
| 9 | `STU-2026-109` | `ethan_williams` | Ethan Williams | `ethan.williams@aurevia.edu` | `BA-COMM` | *(None)* |
| 10 | `STU-2026-110` | `chloe_dubois` | Chloe Dubois | `chloe.dubois@aurevia.edu` | `BA-COMM` | *(None)* |

---

## 4. Seed Data Assessment & Database Invariants

An audit of the live database (`db.sqlite3`) and `seed_demo_data.py` confirmed the existing dataset is rich, coherent, and covers all required university workflows:
- **Users**: 29 active users (President, Provost, Registrar, 3 Deans, 3 HoDs, 4 Faculty, 6 Students, 2 Wardens, IT Director, Admissions Officer, Finance Bursar).
- **Workspace**: Single canonical campus (`Aurevia University — Main Campus`, slug `aurevia-main`).
- **Academic Hierarchy**: 4 Schools (Engineering, Business, Humanities, Computing), 7 Departments.
- **Degree Programmes**: 4 Programmes (B.Tech CSE, B.Tech ECE, Executive MBA, B.A. Media).
- **Class Divisions**: 4 Active sections across semesters 1, 3, and 5.
- **Faculty Teaching Allocations**: 4 Active teaching assignments with schedules and rooms.
- **Admissions Pipeline**: 4 Candidates spanning new submission, admin review, academic review, and approval.
- **Campus Facilities**: Boys' and Girls' residence halls, IT network unit, Bursar office.

**Decision**: The existing dataset is comprehensive and complete. Adding more records would clutter the clean demo UI without adding academic value. Live database records were preserved without changes.

---

## 5. Verification & Test Evidence

### 1. Django System Health Check
- **Command:** `.\venv\Scripts\python.exe manage.py check`
- **Result:** `System check identified no issues (0 silenced).` (Exit code: 0)

### 2. Standalone Importer Logic Simulation
- **Execution:** Parsed `docs/demo/demo_roster_sample.csv` line-by-line using the exact validation rules from `StudentRosterImportView`.
- **Result:** **0 errors, 10 valid rows**. All foreign keys (`Programme`, `ClassDivision`) resolved cleanly against `aurevia-main`.

### 3. Isolated End-to-End HTTP View Upload Test
- **Execution:** Simulated multipart file upload to `/college/students/import/` authenticated as `president_vance` inside an atomic transaction with forced rollback.
- **Result:**
  - Status Code: **HTTP 302** (Redirected to `/college/students/`)
  - Database Insertion: **10 student profiles and 10 users successfully created**.
  - Rollback: Transaction rolled back cleanly; live database verified untouched (User count = 29, Student count = 6).

### 4. Automated Unit Test Verification
- **Command:** `.\venv\Scripts\python.exe manage.py test academics.tests.Phase3AcademicManagementTests.test_roster_csv_import_success_and_duplicates`
- **Result:** `Ran 1 test in 6.319s. OK` (Exit code: 0)

---

## 6. Remaining Limitations & Evaluator Notes

1. **One-Time Import Limitation**: The sample CSV can be imported once into any live database. Re-uploading the exact same CSV file without resetting will correctly trigger duplicate validation error banners, demonstrating the importer's robustness.
2. **Permission Boundary**: Only users holding an Institutional Executive role (`president_vance`, `provost_pendelton`, `registrar_hayes`) or workspace owner status can perform roster imports. Faculty or students attempting access are redirected or blocked.

---

```
================================================================================
                                 STOP POINT
  Task 2 is complete. Verified demo roster sample is ready in docs/demo/.
  Per instructions, execution has halted here. Task 3 has not been started.
================================================================================
```

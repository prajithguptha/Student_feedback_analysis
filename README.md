# B.Tech Course Feedback & Subject Analytics System (Python Hub)

A web-based Academic Feedback and Analytics System developed for **B.Tech Engineering Courses**, featuring **Python Programming & Application Development (CS301)** as its core featured subject.

The system incorporates structured 5-question multi-criteria evaluations with dedicated message boxes for each question, interactive data visualizations (Radar & Distribution charts), a draggable **Floating Window Widget**, role-based security ensuring **only faculty administrators can view student feedback details and identities**, and an academic **Help Desk**.

---

## Key Features & Highlights

### 1. Dual Role-Based Dashboards
- **Student Dashboard**:
  - Overview of all enrolled B.Tech semester subjects (Python Programming featured).
  - Real-time progress bar (e.g. `2 / 5 Completed`).
  - Status indicators (`Submitted` with calculated score vs. `Action Required`).
  - Direct 1-click links to fill feedback or update responses.
- **Admin Dashboard (Confidential)**:
  - Department KPIs: Total Students Enrolled, Total Feedbacks Received, Department Satisfaction Index, Open Help Desk Tickets.
  - Comprehensive **Subject Performance Matrix** showing average ratings across all 5 syllabus dimensions.
  - Recent Student Submissions activity log with student names, roll numbers, and quick inspection links.
  - 1-click **Export Accreditation CSV / Excel** report.

### 2. Interactive Draggable Floating Window
- Positioned at the bottom-right corner across all pages with notification badges.
- **Draggable Header**: Can be repositioned anywhere on screen.
- **Dual Tabs**:
  1. **Subject Status**: Quick overview of all subjects, submission status, and direct shortcuts to fill feedback or view analysis.
  2. **Quick Help Desk Assistant**: Instant answers to common Python course questions, IDE setup guidelines, and direct access to the help desk.
- Minimize, expand, and close toggles.

### 3. Feedback Form (5 Questions with 1 Optional & Dedicated Message Boxes)
Each subject evaluation consists of 5 academic dimensions. **Every single question includes a 1-5 star rating and a dedicated message box (textarea)**:
- **Question 1 (Required)**: *Course Curriculum & Syllabus Coverage*
  - Rating: 1 to 5 Stars
  - Dedicated Message Box: Specific remarks on syllabus depth, Python fundamentals, OOP, and data structures.
- **Question 2 (Required)**: *Teaching Methodology & Live Code Demonstrations*
  - Rating: 1 to 5 Stars
  - Dedicated Message Box: Remarks on instructor live coding pace, PyCharm/VS Code walkthroughs, and error debugging.
- **Question 3 (Required)**: *Pace of Instruction & Doubt Resolution*
  - Rating: 1 to 5 Stars
  - Dedicated Message Box: Feedback on lecture pacing and doubt clearance.
- **Question 4 (Required)**: *Hands-on Laboratory Exercises & Mini-Projects*
  - Rating: 1 to 5 Stars
  - Dedicated Message Box: Comments on practical lab tasks, test cases, and Flask web applications.
- **Question 5 (OPTIONAL)**: *Industry Readiness, Modern Frameworks & Electives*
  - **Explicitly Optional**: Student can submit with or without rating this question.
  - Rating: 1 to 5 Stars (Optional)
  - Dedicated Message Box: (Optional) Recommendations for modern frameworks (FastAPI, Django, PyTorch, Pandas, Docker) for syllabus updates.

### 4. Subject Analysis & Visual Analytics
- Subject switcher dropdown (defaults to **CS301: Python Programming**).
- Quantitative metrics: Overall Course Rating, Satisfaction Percentage, Response Count, Q5 Participation Rate.
- **Chart.js Visualizations**:
  - **5-Dimension Radar / Spider Chart**: Compares the 5 evaluation criteria on a 0-5 scale.
  - **Frequency Bar Chart**: Star rating distribution from 5 Stars down to 1 Star.
- **Strict Role-Based Privacy Boundary**:
  - **Students**: View aggregated statistical scores and visual charts. Individual student identities and raw message box notes are hidden to protect student privacy.
  - **Admins**: Granted full access to the complete student log including Student Full Names, University Roll Numbers, Star Ratings, and verbatim Message Box comments.

### 5. Admin-Only Student Feedback Directory
- Accessible at `/admin/feedbacks` (guarded by `@admin_required`).
- Filter by B.Tech subject or search by student name, roll number, or keywords.
- Modal detail view allowing faculty admins to inspect all 5 questions and their respective message box contents.
- CSV export endpoint (`/admin/export_csv`) generating formatted spreadsheets for NBA / NAAC accreditation.

### 6. Course Help Desk & Query Resolution
- Integrated ticketing system for students to raise questions regarding:
  - Python Course Doubts
  - Technical Lab & Virtual Environment Permissions
  - Mini-Project Guidelines
  - Feedback Form Queries
- Admin queue with status toggle (`Open`, `In Progress`, `Resolved`) and response box.
- B.Tech Python FAQs accordion for instant self-service assistance.

---

## Pre-Configured Demo Accounts

For grading and quick demonstration, the login page (`/login`) includes **1-Click Demo Sign In buttons**:

| Role | Username | Password | Full Name / Roll Number | Access / Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Dr. Rajesh Sharma (HOD / Admin) | Can view all confidential student feedback details, message boxes, and export CSV. |
| **Student** | `rahul_verma` | `student123` | Rahul Verma (21BCE101) | Has completed Python feedback, can view student dashboard and subject analysis. |
| **Student** | `sneha_patel` | `student123` | Sneha Patel (21BCE102) | Has submitted feedback, can edit responses. |
| **Student** | `vikram_aditya` | `student123` | Vikram Aditya (21BCE105) | Has pending feedback for subjects, ideal for testing new feedback submission. |

Students can also self-register via the **Student Registration** page (`/register`).

---

## Project Structure

```
btech_feedback_system/
├── app.py                     # Flask application routes, auth, APIs, and business logic
├── models.py                  # SQLite schema, database helpers, and rich seed data
├── requirements.txt           # Project dependencies (Flask, Werkzeug)
├── run.bat                    # Windows 1-click batch launcher
├── run.ps1                    # PowerShell launcher
├── test_system.py             # Automated unit test suite (100% passing)
├── feedback_system.db         # Pre-seeded SQLite database
├── templates/
│   ├── base.html              # Base layout with Tailwind CSS & Draggable Floating Window
│   ├── index.html             # Home page featuring Python subject & evaluation cycle
│   ├── login.html             # Authentication with 1-click quick demo accounts
│   ├── register.html          # Student registration with roll number
│   ├── dashboard_student.html # Student progress dashboard
│   ├── dashboard_admin.html   # Admin executive dashboard & subject performance table
│   ├── feedback_form.html     # 5-Question form with 1 optional & dedicated message boxes
│   ├── analysis.html          # Subject Analysis with Chart.js Radar & Bar charts
│   ├── admin_feedbacks.html   # Admin-only student feedback directory & modal inspector
│   └── helpdesk.html          # Help Desk ticketing, replies, and Python FAQs
└── static/
    ├── css/
    │   └── style.css          # Custom animations, star rating styles & scrollbars
    └── js/
        └── floating_window.js # Floating window dragging, tabs, and minimize logic
```

---

## How to Run the Application

### Option 1: 1-Click Launch (Windows)
Double-click `run.bat` or execute in PowerShell:
```powershell
.\run.ps1
```

### Option 2: Command Line
```powershell
cd C:\Users\gurra\.gemini\antigravity\scratch\btech_feedback_system
python app.py
```
Then open your web browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## Running the Automated Test Suite

To verify all routes, access controls, feedback calculations, and permissions:
```powershell
cd C:\Users\gurra\.gemini\antigravity\scratch\btech_feedback_system
python test_system.py
```
All 6 comprehensive unit tests will execute and confirm system integrity.

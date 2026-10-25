# EduPulse — Student Course Feedback Analysis System

A responsive student feedback dashboard inspired by the supplied reference image. Students can submit anonymous ratings for CDCT, PEDH, IDSA, OS, and DBMS. The dashboard updates animated charts and aggregated reports immediately after each valid submission.

## Features

- Responsive navy/purple dashboard, mobile-friendly navigation
- Five courses and five required 1–5 rating questions per submission
- Optional comment field (maximum 500 characters)
- Server-side validation and JSON API endpoints
- Local demo storage in `data/feedback.json` so the project works without MySQL setup
- Animated Chart.js course comparison, rating distribution, question averages, and response counts
- CSV export of course-wise aggregated report
- Pandas, NumPy, and Matplotlib analysis script
- MySQL schema and seed data in `database.sql`
- Anonymous-by-design: no student name, email, or IP address is requested or stored
- Small-group suppression: course-level ratings are hidden for groups with fewer than five submissions; raw comments are never exposed on the dashboard or in the aggregate CSV

## Run locally

Python 3.10+ recommended.

### Windows

1. Extract the ZIP.
2. Open Command Prompt or PowerShell in the project folder.
3. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

4. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

5. Start the website:

   ```powershell
   python app.py
   ```

6. Open `http://127.0.0.1:5000` in your browser.

**Demo mode works without MySQL.** Feedback is saved in `data/feedback.json`. Keep the file private if you share the project folder because it contains optional comments.

## MySQL setup

1. Open MySQL Workbench.
2. Run `database.sql` to create the `student_feedback` database, three requested tables, and seed courses/questions.
3. The included website currently uses local JSON storage for a zero-configuration demo. To switch the app to MySQL persistence, implement the DB connection in `app.py` using `mysql-connector-python` and environment variables; do not commit database credentials. The schema is included and ready for that integration.

## Generate analysis reports

Submit some feedback first, then run:

```bash
python analysis.py
```

Generated aggregated CSV reports and PNG charts are saved under `reports/`. Install the requirements first. For privacy, reports suppress course averages for fewer than five submissions and never include comments.

## API

- `GET /api/summary` — aggregated dashboard metrics (comments are not returned)
- `POST /api/feedback` — validates and stores a submission
- `GET /api/export.csv` — downloads aggregated course report
- `GET /health` — simple health check

Example JSON body for `POST /api/feedback`:

```json
{
  "course_code": "DBMS",
  "ratings": [5, 4, 5, 4, 5],
  "comment": "More practical examples would be useful."
}
```

Every rating must be an integer from 1 to 5 and all five questions are required.

## Privacy note

Anonymous reporting reduces but cannot guarantee anonymity. Avoid putting names, personal stories, or identifying details in comments. Suppression is applied to course-level summaries for fewer than five submissions. In a small cohort, even aggregate results may reveal information, so follow your institution's privacy policy before publishing results.

## Project structure

```text
Student_Course_Feedback_Analysis_System/
├── app.py
├── analysis.py
├── database.sql
├── requirements.txt
├── README.md
├── data/
│   └── feedback.json
├── reports/
├── static/
│   ├── app.js
│   └── style.css
└── templates/
    └── index.html
```

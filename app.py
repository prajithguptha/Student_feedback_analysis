from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timezone
from pathlib import Path
import csv, io, json, os, statistics

BASE_DIR = Path(__file__).resolve().parent
# On Vercel (and similar serverless hosts) the project folder is read-only, so
# feedback is written to the writable /tmp folder instead. Locally it stays in ./data.
if os.environ.get("VERCEL") or not os.access(BASE_DIR, os.W_OK):
    DATA_DIR = Path("/tmp/feedback_data")
else:
    DATA_DIR = BASE_DIR / "data"
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    DATA_DIR = Path("/tmp/feedback_data"); DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "feedback.json"

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Minimum submissions before a course's averages are shown (privacy threshold).
# Set to 1 so charts work with any data; raise to 5 for strict anonymity in real use.
MIN_RESPONSES = 1

COURSES = [
    {"id": 1, "code": "CDCT", "name": "Communication Excellence and Soft Skills"},
    {"id": 2, "code": "PEDH", "name": "Python Essentials for Data Handling and Web Integration"},
    {"id": 3, "code": "IDSA", "name": "Industry Data Structures and Algorithms"},
    {"id": 4, "code": "OS", "name": "Operating Systems"},
    {"id": 5, "code": "DBMS", "name": "Database Management Systems"},
]
QUESTIONS = [
    "How clearly are the subject concepts explained?",
    "How effective are the teaching methods and examples?",
    "How well does the course content match the syllabus?",
    "How helpful are the assignments, practicals, and learning materials?",
    "Overall, how satisfied are you with this course?",
]

def load_feedback():
    if not DATA_FILE.exists():
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def save_feedback(rows):
    DATA_FILE.write_text(json.dumps(rows, indent=2), encoding="utf-8")

def summarize(rows):
    # Aggregate only. Raw comments are deliberately not returned to the dashboard.
    summaries = []
    for course in COURSES:
        course_rows = [r for r in rows if r.get("course_code") == course["code"]]
        all_ratings = [int(rating) for row in course_rows for rating in row.get("ratings", [])]
        q_averages = []
        for qi in range(len(QUESTIONS)):
            vals = [int(r["ratings"][qi]) for r in course_rows if len(r.get("ratings", [])) > qi]
            q_averages.append(round(sum(vals) / len(vals), 2) if vals else 0)
        dist = {str(i): sum(1 for val in all_ratings if val == i) for i in range(1, 6)}
        summaries.append({
            "code": course["code"], "name": course["name"],
            "responses": len(course_rows),
            "average": round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else 0,
            "question_averages": q_averages,
            "distribution": dist,
        })
    all_ratings = [int(rating) for row in rows for rating in row.get("ratings", [])]
    total_answers = len(all_ratings)
    distribution = {str(i): sum(1 for val in all_ratings if val == i) for i in range(1, 6)}
    # Privacy: hide detailed course averages when there are fewer than 5 submissions.
    privacy_summaries = []
    for s in summaries:
        item = dict(s)
        if 0 < item["responses"] < MIN_RESPONSES:
            item["average"] = None
            item["question_averages"] = [None] * len(QUESTIONS)
            item["distribution"] = {str(i): 0 for i in range(1, 6)}
            item["suppressed"] = True
        else:
            item["suppressed"] = False
        privacy_summaries.append(item)
    return {
        "total_responses": len(rows),
        "total_ratings": total_answers,
        "overall_average": round(sum(all_ratings) / total_answers, 2) if total_answers else 0,
        "distribution": distribution,
        "courses": privacy_summaries,
        "questions": QUESTIONS,
        "course_count": len(COURSES),
    }

@app.route("/")
def index():
    return render_template("index.html", courses=COURSES, questions=QUESTIONS)

@app.get("/api/summary")
def api_summary():
    return jsonify(summarize(load_feedback()))

@app.post("/api/feedback")
def submit_feedback():
    payload = request.get_json(silent=True) or {}
    course_code = str(payload.get("course_code", "")).strip().upper()
    course = next((c for c in COURSES if c["code"] == course_code), None)
    ratings = payload.get("ratings")
    comment = str(payload.get("comment", "")).strip()
    if not course:
        return jsonify({"error": "Please choose a valid course."}), 400
    if not isinstance(ratings, list) or len(ratings) != len(QUESTIONS):
        return jsonify({"error": "Please answer all five questions."}), 400
    clean_ratings = []
    for rating in ratings:
        if isinstance(rating, bool) or not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({"error": "Every rating must be a whole number from 1 to 5."}), 400
        clean_ratings.append(rating)
    if len(comment) > 500:
        return jsonify({"error": "Comments must be 500 characters or fewer."}), 400
    rows = load_feedback()
    rows.append({
        "feedback_id": (max([r.get("feedback_id", 0) for r in rows], default=0) + 1),
        "course_code": course_code,
        "ratings": clean_ratings,
        "comment": comment,
        "submitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    save_feedback(rows)
    return jsonify({"message": "Feedback submitted successfully. Thank you!", "summary": summarize(rows)}), 201

@app.errorhandler(Exception)
def handle_error(err):
    # Always answer API calls with JSON so the page shows a readable message.
    from werkzeug.exceptions import HTTPException
    if request.path.startswith("/api/"):
        code = err.code if isinstance(err, HTTPException) else 500
        return jsonify({"error": "Server error while saving feedback. Please try again."}), code
    if isinstance(err, HTTPException):
        return err
    raise err

@app.get("/api/export.csv")
def export_csv():
    rows = load_feedback()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Course Code", "Course Name", "Responses", "Average Rating", *[f"Q{i+1} Average" for i in range(5)]])
    summary = summarize(rows)
    for item in summary["courses"]:
        # Do not export small-group suppressed statistics.
        if item["suppressed"]:
            writer.writerow([item["code"], item["name"], item["responses"], "Suppressed", *["Suppressed"] * 5])
        else:
            writer.writerow([item["code"], item["name"], item["responses"], item["average"], *item["question_averages"]])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8-sig")), mimetype="text/csv",
                     as_attachment=True, download_name="course_feedback_summary.csv")

@app.get("/health")
def health():
    return jsonify({"status": "ok", "storage": "local JSON demo mode", "mysql_schema": "database.sql"})

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))

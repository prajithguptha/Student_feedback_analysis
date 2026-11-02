import os
import csv
import io
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, Response, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from models import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = 'btech-python-feedback-portal-secret-key-2026'

# Initialize and seed database on startup if not present
with app.app_context():
    init_db()
    seed_db()

# ----------------- AUTH HELPERS -----------------

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in as Admin to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        if session.get('user_role') != 'admin':
            flash("Access denied: Only Administrators can view student feedback details.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_globals():
    current_user = get_current_user()
    conn = get_db()
    subjects = conn.execute("SELECT * FROM subjects ORDER BY is_featured DESC, id ASC").fetchall()
    
    # Calculate quick stats for floating window
    pending_feedbacks = 0
    completed_feedbacks = 0
    if current_user and current_user['role'] == 'student':
        submitted_ids = conn.execute(
            "SELECT subject_id FROM feedbacks WHERE user_id = ?", (current_user['id'],)
        ).fetchall()
        submitted_set = {row['subject_id'] for row in submitted_ids}
        completed_feedbacks = len(submitted_set)
        pending_feedbacks = max(0, len(subjects) - completed_feedbacks)
    
    conn.close()
    return dict(
        current_user=current_user,
        global_subjects=subjects,
        pending_feedbacks_count=pending_feedbacks,
        completed_feedbacks_count=completed_feedbacks,
        current_year=datetime.now().year
    )

# ----------------- AUTH ROUTES -----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_role'] = user['role']
            session['user_name'] = user['full_name']
            flash(f"Welcome back, {user['full_name']}! Signed in as {user['role'].capitalize()}.", "success")
            
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password. Please try again.", "danger")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        roll_no = request.form.get('roll_no', '').strip().upper()
        email = request.form.get('email', '').strip().lower()
        branch = request.form.get('branch', 'Computer Science & Engineering')
        semester = request.form.get('semester', 'B.Tech 5th Semester')
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not (full_name and username and roll_no and email and password):
            flash("All mandatory fields must be filled.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ? OR roll_no = ?",
            (username, email, roll_no)
        ).fetchone()

        if existing:
            flash("Username, Email or Roll Number already registered. Please login.", "warning")
            conn.close()
            return render_template('register.html')

        hashed_pw = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO users (username, password_hash, full_name, roll_no, email, role, branch, semester)
        VALUES (?, ?, ?, ?, ?, 'student', ?, ?)
        ''', (username, hashed_pw, full_name, roll_no, email, branch, semester))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        session['user_id'] = user_id
        session['username'] = username
        session['user_role'] = 'student'
        session['user_name'] = full_name

        flash("Student account created successfully! Welcome to the B.Tech Course Feedback Portal.", "success")
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('login'))

# ----------------- MAIN PAGES -----------------

@app.route('/')
def home():
    conn = get_db()
    # Featured Python subject details
    python_subject = conn.execute("SELECT * FROM subjects WHERE is_featured = 1 LIMIT 1").fetchone()
    all_subjects = conn.execute("SELECT * FROM subjects ORDER BY is_featured DESC").fetchall()
    
    # Aggregated feedback stats for landing page showcase
    stats = conn.execute('''
        SELECT 
            COUNT(id) as total_feedbacks,
            COALESCE(AVG(overall_score), 0) as avg_rating,
            COUNT(DISTINCT user_id) as total_students_participated
        FROM feedbacks
    ''').fetchone()
    
    conn.close()
    return render_template('index.html', python_subject=python_subject, all_subjects=all_subjects, stats=stats)

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    conn = get_db()

    if user['role'] == 'admin':
        # Admin Dashboard: High-level overview, subject metrics, recent feedbacks
        total_students = conn.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'").fetchone()['count']
        total_feedbacks = conn.execute("SELECT COUNT(*) as count FROM feedbacks").fetchone()['count']
        overall_avg = conn.execute("SELECT COALESCE(AVG(overall_score), 0) as avg FROM feedbacks").fetchone()['avg']
        open_tickets = conn.execute("SELECT COUNT(*) as count FROM help_desk_tickets WHERE status != 'Resolved'").fetchone()['count']

        # Subject-wise stats
        subject_stats = conn.execute('''
            SELECT 
                s.id, s.code, s.name, s.instructor, s.is_featured,
                COUNT(f.id) as response_count,
                COALESCE(AVG(f.overall_score), 0) as avg_score,
                COALESCE(AVG(f.q1_score), 0) as avg_q1,
                COALESCE(AVG(f.q2_score), 0) as avg_q2,
                COALESCE(AVG(f.q3_score), 0) as avg_q3,
                COALESCE(AVG(f.q4_score), 0) as avg_q4,
                COALESCE(AVG(f.q5_score), 0) as avg_q5
            FROM subjects s
            LEFT JOIN feedbacks f ON s.id = f.subject_id
            GROUP BY s.id
            ORDER BY s.is_featured DESC, avg_score DESC
        ''').fetchall()

        # Recent student feedbacks (Admin only can see student info)
        recent_feedbacks = conn.execute('''
            SELECT 
                f.id, f.overall_score, f.submitted_at,
                u.full_name, u.roll_no,
                s.name as subject_name, s.code as subject_code
            FROM feedbacks f
            JOIN users u ON f.user_id = u.id
            JOIN subjects s ON f.subject_id = s.id
            ORDER BY f.submitted_at DESC
            LIMIT 6
        ''').fetchall()

        conn.close()
        return render_template(
            'dashboard_admin.html',
            total_students=total_students,
            total_feedbacks=total_feedbacks,
            overall_avg=round(overall_avg, 2),
            open_tickets=open_tickets,
            subject_stats=subject_stats,
            recent_feedbacks=recent_feedbacks
        )
    else:
        # Student Dashboard: List of subjects, feedback completion status, action links
        subjects_data = conn.execute('''
            SELECT 
                s.id, s.code, s.name, s.instructor, s.description, s.is_featured, s.credits,
                f.id as feedback_id,
                f.overall_score,
                f.submitted_at
            FROM subjects s
            LEFT JOIN feedbacks f ON s.id = f.subject_id AND f.user_id = ?
            ORDER BY s.is_featured DESC, s.id ASC
        ''', (user['id'],)).fetchall()

        total_subjects = len(subjects_data)
        completed = sum(1 for s in subjects_data if s['feedback_id'] is not None)
        pending = total_subjects - completed
        completion_pct = int((completed / total_subjects * 100) if total_subjects else 0)

        conn.close()
        return render_template(
            'dashboard_student.html',
            subjects=subjects_data,
            total_subjects=total_subjects,
            completed=completed,
            pending=pending,
            completion_pct=completion_pct
        )

# ----------------- FEEDBACK MODULE -----------------

@app.route('/feedback/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def feedback_form(subject_id):
    user = get_current_user()
    if user['role'] == 'admin':
        flash("Faculty Administrators do not submit student feedback. Viewing Subject Analysis instead.", "info")
        return redirect(url_for('subject_analysis', subject_id=subject_id))

    conn = get_db()
    subject = conn.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    if not subject:
        conn.close()
        abort(404)

    # Check if student has already submitted feedback
    existing_feedback = conn.execute(
        "SELECT * FROM feedbacks WHERE user_id = ? AND subject_id = ?",
        (user['id'], subject_id)
    ).fetchone()

    if request.method == 'POST':
        # 5 Questions: Q1-Q4 required, Q5 optional.
        # Each question has a score (1-5) and a dedicated message box.
        try:
            q1_score = int(request.form.get('q1_score', 0))
            q2_score = int(request.form.get('q2_score', 0))
            q3_score = int(request.form.get('q3_score', 0))
            q4_score = int(request.form.get('q4_score', 0))
        except ValueError:
            flash("Please provide ratings for all required questions (Questions 1 to 4).", "danger")
            conn.close()
            return render_template('feedback_form.html', subject=subject, feedback=existing_feedback)

        # Optional Q5
        q5_score_raw = request.form.get('q5_score')
        q5_score = int(q5_score_raw) if (q5_score_raw and q5_score_raw.isdigit() and int(q5_score_raw) > 0) else None

        # Message boxes for each question
        q1_message = request.form.get('q1_message', '').strip()
        q2_message = request.form.get('q2_message', '').strip()
        q3_message = request.form.get('q3_message', '').strip()
        q4_message = request.form.get('q4_message', '').strip()
        q5_message = request.form.get('q5_message', '').strip()

        # Validate required scores 1-5
        if not (1 <= q1_score <= 5 and 1 <= q2_score <= 5 and 1 <= q3_score <= 5 and 1 <= q4_score <= 5):
            flash("Questions 1 through 4 require a rating between 1 and 5 stars.", "danger")
            conn.close()
            return render_template('feedback_form.html', subject=subject, feedback=existing_feedback)

        # Compute overall score
        scores = [q1_score, q2_score, q3_score, q4_score]
        if q5_score:
            scores.append(q5_score)
        overall_score = round(sum(scores) / len(scores), 2)

        cursor = conn.cursor()
        if existing_feedback:
            # Update existing feedback
            cursor.execute('''
                UPDATE feedbacks
                SET q1_score = ?, q1_message = ?,
                    q2_score = ?, q2_message = ?,
                    q3_score = ?, q3_message = ?,
                    q4_score = ?, q4_message = ?,
                    q5_score = ?, q5_message = ?,
                    overall_score = ?,
                    submitted_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (q1_score, q1_message, q2_score, q2_message, q3_score, q3_message,
                  q4_score, q4_message, q5_score, q5_message, overall_score, existing_feedback['id']))
            flash(f"Your feedback for {subject['name']} has been updated successfully!", "success")
        else:
            # Insert new feedback
            cursor.execute('''
                INSERT INTO feedbacks (
                    user_id, subject_id,
                    q1_score, q1_message,
                    q2_score, q2_message,
                    q3_score, q3_message,
                    q4_score, q4_message,
                    q5_score, q5_message,
                    overall_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user['id'], subject_id,
                  q1_score, q1_message,
                  q2_score, q2_message,
                  q3_score, q3_message,
                  q4_score, q4_message,
                  q5_score, q5_message,
                  overall_score))
            flash(f"Thank you! Your feedback for {subject['name']} has been submitted successfully.", "success")

        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('feedback_form.html', subject=subject, feedback=existing_feedback)

# ----------------- SUBJECT ANALYSIS MODULE -----------------

@app.route('/analysis')
@app.route('/analysis/<int:subject_id>')
def subject_analysis(subject_id=None):
    conn = get_db()
    current_user = get_current_user()

    # Default to featured subject (Python) if subject_id is not specified
    if not subject_id:
        featured = conn.execute("SELECT id FROM subjects WHERE is_featured = 1 LIMIT 1").fetchone()
        subject_id = featured['id'] if featured else 1

    subject = conn.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    if not subject:
        conn.close()
        abort(404)

    all_subjects = conn.execute("SELECT id, code, name, is_featured FROM subjects ORDER BY is_featured DESC, id ASC").fetchall()

    # Aggregate metrics for this subject
    feedbacks = conn.execute('''
        SELECT f.*, u.full_name, u.roll_no, u.branch, u.semester
        FROM feedbacks f
        JOIN users u ON f.user_id = u.id
        WHERE f.subject_id = ?
        ORDER BY f.submitted_at DESC
    ''', (subject_id,)).fetchall()

    total_responses = len(feedbacks)
    
    # Calculate detailed averages per question
    avg_overall = 0.0
    avg_q1 = 0.0
    avg_q2 = 0.0
    avg_q3 = 0.0
    avg_q4 = 0.0
    avg_q5 = 0.0
    q5_count = 0
    
    rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}

    if total_responses > 0:
        avg_overall = sum(f['overall_score'] for f in feedbacks) / total_responses
        avg_q1 = sum(f['q1_score'] for f in feedbacks) / total_responses
        avg_q2 = sum(f['q2_score'] for f in feedbacks) / total_responses
        avg_q3 = sum(f['q3_score'] for f in feedbacks) / total_responses
        avg_q4 = sum(f['q4_score'] for f in feedbacks) / total_responses
        
        q5_scores = [f['q5_score'] for f in feedbacks if f['q5_score'] is not None]
        q5_count = len(q5_scores)
        avg_q5 = (sum(q5_scores) / q5_count) if q5_count > 0 else 0.0

        for f in feedbacks:
            rounded_star = int(round(f['overall_score']))
            rounded_star = max(1, min(5, rounded_star))
            rating_distribution[rounded_star] += 1

    is_admin = current_user and current_user['role'] == 'admin'

    # Filtered feedbacks list: ONLY admin can see student identity and detailed individual responses
    admin_feedbacks_list = feedbacks if is_admin else []

    conn.close()
    return render_template(
        'analysis.html',
        subject=subject,
        all_subjects=all_subjects,
        total_responses=total_responses,
        avg_overall=round(avg_overall, 2),
        satisfaction_pct=round((avg_overall / 5.0) * 100, 1) if avg_overall else 0,
        avg_q1=round(avg_q1, 2),
        avg_q2=round(avg_q2, 2),
        avg_q3=round(avg_q3, 2),
        avg_q4=round(avg_q4, 2),
        avg_q5=round(avg_q5, 2),
        q5_count=q5_count,
        rating_distribution=rating_distribution,
        is_admin=is_admin,
        admin_feedbacks_list=admin_feedbacks_list
    )

# ----------------- ADMIN ONLY FEEDBACK REVIEW -----------------

@app.route('/admin/feedbacks')
@admin_required
def admin_feedbacks():
    subject_id = request.args.get('subject_id')
    search_query = request.args.get('q', '').strip()

    conn = get_db()
    all_subjects = conn.execute("SELECT id, code, name FROM subjects ORDER BY is_featured DESC").fetchall()

    query = '''
        SELECT 
            f.*,
            u.full_name, u.roll_no, u.email, u.branch, u.semester as user_semester,
            s.code as subject_code, s.name as subject_name
        FROM feedbacks f
        JOIN users u ON f.user_id = u.id
        JOIN subjects s ON f.subject_id = s.id
        WHERE 1=1
    '''
    params = []

    if subject_id and subject_id.isdigit():
        query += ' AND f.subject_id = ?'
        params.append(int(subject_id))

    if search_query:
        query += ' AND (u.full_name LIKE ? OR u.roll_no LIKE ? OR f.q1_message LIKE ? OR f.q2_message LIKE ? OR f.q3_message LIKE ? OR f.q4_message LIKE ? OR f.q5_message LIKE ?)'
        wildcard = f"%{search_query}%"
        params.extend([wildcard] * 7)

    query += ' ORDER BY f.submitted_at DESC'
    feedbacks = conn.execute(query, params).fetchall()

    conn.close()
    return render_template(
        'admin_feedbacks.html',
        feedbacks=feedbacks,
        all_subjects=all_subjects,
        selected_subject=int(subject_id) if (subject_id and subject_id.isdigit()) else None,
        search_query=search_query
    )

@app.route('/admin/export_csv')
@admin_required
def export_csv():
    conn = get_db()
    rows = conn.execute('''
        SELECT 
            u.roll_no, u.full_name, u.email, u.branch,
            s.code as subject_code, s.name as subject_name,
            f.overall_score,
            f.q1_score, f.q1_message,
            f.q2_score, f.q2_message,
            f.q3_score, f.q3_message,
            f.q4_score, f.q4_message,
            f.q5_score, f.q5_message,
            f.submitted_at
        FROM feedbacks f
        JOIN users u ON f.user_id = u.id
        JOIN subjects s ON f.subject_id = s.id
        ORDER BY s.code, f.submitted_at DESC
    ''').fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Roll No', 'Student Name', 'Email', 'Branch',
        'Subject Code', 'Subject Name', 'Overall Score',
        'Q1 Curriculum Score', 'Q1 Remarks (Message Box)',
        'Q2 Methodology Score', 'Q2 Remarks (Message Box)',
        'Q3 Pace Score', 'Q3 Remarks (Message Box)',
        'Q4 Labs/Projects Score', 'Q4 Remarks (Message Box)',
        'Q5 Industry/Elective Score (Optional)', 'Q5 Remarks (Message Box)',
        'Submission Timestamp'
    ])

    for r in rows:
        writer.writerow([
            r['roll_no'], r['full_name'], r['email'], r['branch'],
            r['subject_code'], r['subject_name'], r['overall_score'],
            r['q1_score'], r['q1_message'],
            r['q2_score'], r['q2_message'],
            r['q3_score'], r['q3_message'],
            r['q4_score'], r['q4_message'],
            r['q5_score'] if r['q5_score'] is not None else 'N/A', r['q5_message'],
            r['submitted_at']
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=btech_feedback_report.csv"}
    )

# ----------------- HELP DESK MODULE -----------------

@app.route('/helpdesk', methods=['GET', 'POST'])
@login_required
def helpdesk():
    user = get_current_user()
    conn = get_db()

    if request.method == 'POST':
        # New ticket creation
        title = request.form.get('title', '').strip()
        category = request.form.get('category', 'General')
        subject_id_raw = request.form.get('subject_id')
        subject_id = int(subject_id_raw) if (subject_id_raw and subject_id_raw.isdigit()) else None
        message = request.form.get('message', '').strip()

        if not (title and message):
            flash("Please provide both a query title and description.", "danger")
        else:
            conn.execute('''
                INSERT INTO help_desk_tickets (user_id, subject_id, title, category, message, status)
                VALUES (?, ?, ?, ?, ?, 'Open')
            ''', (user['id'], subject_id, title, category, message))
            conn.commit()
            flash("Your Help Desk query has been submitted! Our Python academic coordinator will respond shortly.", "success")
            conn.close()
            return redirect(url_for('helpdesk'))

    if user['role'] == 'admin':
        tickets = conn.execute('''
            SELECT t.*, u.full_name, u.roll_no, u.email, s.name as subject_name, s.code as subject_code
            FROM help_desk_tickets t
            JOIN users u ON t.user_id = u.id
            LEFT JOIN subjects s ON t.subject_id = s.id
            ORDER BY 
                CASE t.status 
                    WHEN 'Open' THEN 1 
                    WHEN 'In Progress' THEN 2 
                    ELSE 3 
                END,
                t.created_at DESC
        ''').fetchall()
    else:
        tickets = conn.execute('''
            SELECT t.*, u.full_name, s.name as subject_name, s.code as subject_code
            FROM help_desk_tickets t
            JOIN users u ON t.user_id = u.id
            LEFT JOIN subjects s ON t.subject_id = s.id
            WHERE t.user_id = ?
            ORDER BY t.created_at DESC
        ''', (user['id'],)).fetchall()

    subjects = conn.execute("SELECT id, code, name FROM subjects").fetchall()
    conn.close()
    return render_template('helpdesk.html', tickets=tickets, subjects=subjects)

@app.route('/helpdesk/reply/<int:ticket_id>', methods=['POST'])
@admin_required
def helpdesk_reply(ticket_id):
    reply = request.form.get('admin_reply', '').strip()
    status = request.form.get('status', 'Resolved')

    conn = get_db()
    conn.execute('''
        UPDATE help_desk_tickets
        SET admin_reply = ?, status = ?, replied_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (reply, status, ticket_id))
    conn.commit()
    conn.close()

    flash(f"Ticket #{ticket_id} updated successfully.", "success")
    return redirect(url_for('helpdesk'))

# ----------------- API ENDPOINTS (For Floating Window & Charts) -----------------

@app.route('/api/quick-status')
def api_quick_status():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False})
    
    conn = get_db()
    subjects = conn.execute("SELECT id, code, name, is_featured FROM subjects ORDER BY is_featured DESC").fetchall()
    submitted = conn.execute("SELECT subject_id, overall_score FROM feedbacks WHERE user_id = ?", (user['id'],)).fetchall()
    conn.close()

    submitted_map = {s['subject_id']: s['overall_score'] for s in submitted}
    
    status_list = []
    for s in subjects:
        status_list.append({
            "id": s['id'],
            "code": s['code'],
            "name": s['name'],
            "is_featured": bool(s['is_featured']),
            "has_submitted": s['id'] in submitted_map,
            "overall_score": submitted_map.get(s['id'])
        })

    return jsonify({
        "authenticated": True,
        "role": user['role'],
        "name": user['full_name'],
        "subjects": status_list
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

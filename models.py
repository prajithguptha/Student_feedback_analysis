import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feedback_system.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        roll_no TEXT UNIQUE,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',  -- 'admin' or 'student'
        branch TEXT DEFAULT 'Computer Science & Engineering',
        semester TEXT DEFAULT 'B.Tech 5th Semester',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Subjects table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        instructor TEXT NOT NULL,
        description TEXT,
        semester TEXT DEFAULT 'Semester 5',
        credits INTEGER DEFAULT 4,
        is_featured INTEGER DEFAULT 0
    )
    ''')

    # Feedback table: 5 questions with score & message box each (Q5 optional)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedbacks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        q1_score INTEGER NOT NULL,
        q1_message TEXT,
        q2_score INTEGER NOT NULL,
        q2_message TEXT,
        q3_score INTEGER NOT NULL,
        q3_message TEXT,
        q4_score INTEGER NOT NULL,
        q4_message TEXT,
        q5_score INTEGER,
        q5_message TEXT,
        overall_score REAL NOT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, subject_id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
    )
    ''')

    # Help Desk Tickets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS help_desk_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject_id INTEGER,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'Open',  -- 'Open', 'In Progress', 'Resolved'
        admin_reply TEXT,
        replied_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
    )
    ''')

    conn.commit()
    conn.close()

def seed_db():
    conn = get_db()
    cursor = conn.cursor()

    # Check if admin already exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if cursor.fetchone():
        conn.close()
        return

    # Seed Admin User
    admin_pw = generate_password_hash("admin123")
    cursor.execute('''
    INSERT INTO users (username, password_hash, full_name, roll_no, email, role, branch, semester)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('admin', admin_pw, 'Dr. Rajesh Sharma (HOD / Admin)', 'ADMIN001', 'admin@btech.ac.in', 'admin', 'Computer Science & Engineering', 'Faculty / Admin'))

    # Seed Students
    student_pw = generate_password_hash("student123")
    students = [
        ('rahul_verma', student_pw, 'Rahul Verma', '21BCE101', 'rahul.verma@student.btech.ac.in', 'student', 'CSE', '5th Semester'),
        ('sneha_patel', student_pw, 'Sneha Patel', '21BCE102', 'sneha.patel@student.btech.ac.in', 'student', 'CSE', '5th Semester'),
        ('arjun_nair', student_pw, 'Arjun Nair', '21BCE103', 'arjun.nair@student.btech.ac.in', 'student', 'CSE', '5th Semester'),
        ('priya_sharma', student_pw, 'Priya Sharma', '21BCE104', 'priya.sharma@student.btech.ac.in', 'student', 'CSE', '5th Semester'),
        ('vikram_aditya', student_pw, 'Vikram Aditya', '21BCE105', 'vikram.aditya@student.btech.ac.in', 'student', 'CSE', '5th Semester'),
    ]
    for s in students:
        cursor.execute('''
        INSERT INTO users (username, password_hash, full_name, roll_no, email, role, branch, semester)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', s)

    # Seed Subjects (Python is featured as per project prompt)
    subjects = [
        ('CS301', 'Python Programming & Application Development', 'Prof. Ananya Sen',
         'Comprehensive study of Python 3, object-oriented concepts, functional programming, data analysis with NumPy/Pandas, and web development with Flask.',
         '5th Semester', 4, 1),
        ('CS302', 'Data Structures & Algorithms in Python', 'Dr. Vikram Seth',
         'Implementation of Stacks, Queues, Trees, Graphs, Sorting, Dynamic Programming and complexity analysis in Python.',
         '5th Semester', 4, 0),
        ('CS303', 'Database Management Systems (DBMS)', 'Prof. Murali Krishna',
         'Relational schema design, SQL, Normalization, Transaction management and indexing with SQLite and MySQL integration.',
         '5th Semester', 3, 0),
        ('CS304', 'Operating Systems & System Programming', 'Dr. Harish Rao',
         'Process scheduling, Memory management, Concurrency, Deadlocks and Linux Shell scripting.',
         '5th Semester', 3, 0),
        ('CS305', 'Computer Networks & Protocols', 'Prof. Sangeeta Rao',
         'OSI & TCP/IP stack, Socket programming in Python, routing algorithms, HTTP/HTTPS and network security.',
         '5th Semester', 3, 0)
    ]
    for subj in subjects:
        cursor.execute('''
        INSERT INTO subjects (code, name, instructor, description, semester, credits, is_featured)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', subj)

    conn.commit()

    # Retrieve inserted IDs
    cursor.execute("SELECT id, username FROM users WHERE role = 'student'")
    student_map = {row['username']: row['id'] for row in cursor.fetchall()}

    cursor.execute("SELECT id, code FROM subjects")
    subject_map = {row['code']: row['id'] for row in cursor.fetchall()}

    # Seed sample feedbacks for rich analytics demonstration
    sample_feedbacks = [
        # Student 1: Rahul on Python CS301
        (student_map['rahul_verma'], subject_map['CS301'],
         5, "Syllabus covers OOP, generators, decorators and Flask thoroughly. Very relevant for modern software development.",
         5, "Live coding in PyCharm during class made debugging concepts very clear.",
         4, "Pace was balanced, occasional extra time spent on metaclasses was very helpful.",
         5, "Lab assignments with automated test cases challenged us to write clean PEP-8 code.",
         5, "Would love to have an elective module on FastAPI and async asyncio programming in semester 6.",
         4.8),

        # Student 2: Sneha on Python CS301
        (student_map['sneha_patel'], subject_map['CS301'],
         4, "Good structured syllabus. More focus on Pandas and data visualization would be great.",
         5, "Professor Ananya explains every error trace patiently and demonstrates real-world debugging.",
         4, "Pace is comfortable. Lecture notes with code snippets are shared promptly.",
         4, "The mini-project assignment built our confidence in building web-based tools.",
         4, "Please consider introducing Docker containerization for Python web applications.",
         4.2),

        # Student 3: Arjun on Python CS301
        (student_map['arjun_nair'], subject_map['CS301'],
         5, "Extremely practical curriculum. Loved the transition from scripting to full-stack.",
         4, "Great demonstrations on data structures and object models.",
         5, "Clear voice, well-organized slides, and regular doubt clearing sessions on Fridays.",
         5, "Lab questions were engaging and inspired us to explore GitHub repositories.",
         None, "",  # Optional question left blank
         4.75),

        # Student 4: Priya on Python CS301
        (student_map['priya_sharma'], subject_map['CS301'],
         4, "Strong coverage of Python core. Would like a bit more time allocated to unit testing with pytest.",
         4, "Code walkthroughs are clear and interactive.",
         4, "Instructor answers all questions in class without rushing through slides.",
         4, "Lab tasks had practical utility such as web scrapers and REST API endpoints.",
         5, "Include PyTorch or Machine Learning basics in the elective track.",
         4.2),

        # Sample feedbacks on other subjects for comparison
        (student_map['rahul_verma'], subject_map['CS302'],
         4, "DSA problem sets were rigorous and competitive.",
         4, "Good visualization of binary search trees and heap algorithms.",
         3, "Pace was slightly fast during graph algorithms and dynamic programming.",
         4, "Practical lab submissions on LeetCode/HackerRank were very motivating.",
         None, "Provide more mock interview problem sheets.",
         3.75),

        (student_map['sneha_patel'], subject_map['CS303'],
         5, "SQL queries, joins, and normalization examples were explained very thoroughly.",
         4, "Interactive queries executed on MySQL during live class.",
         5, "Pacing was spot on. Easy to follow ER diagrams.",
         4, "Connecting Python backend to MySQL in lab 4 was a great exercise.",
         4, "Introduce NoSQL / MongoDB concepts in future semesters.",
         4.4)
    ]

    for fb in sample_feedbacks:
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
        ''', (fb[0], fb[1], fb[2], fb[3], fb[4], fb[5], fb[6], fb[7], fb[8], fb[9], fb[10], fb[11], fb[12]))

    # Seed Sample Help Desk Tickets
    tickets = [
        (student_map['arjun_nair'], subject_map['CS301'],
         'Python Virtualenv Setup Issue in Lab PC', 'Technical Lab Issue',
         'While running pip install -r requirements.txt in the college computer lab, getting an access permission error on Python 3.12.',
         'Resolved',
         'The lab technician has updated the execution policy. Please run your virtual environments in D:\\students\\ folder.',
         '2026-10-28 14:30:00'),
        (student_map['sneha_patel'], subject_map['CS301'],
         'Query regarding Question 5 Optional Field in Feedback Form', 'Feedback Portal Query',
         'Is Question 5 compulsory to answer for B.Tech accreditation score, or can we submit with only Q1-Q4 filled?',
         'Resolved',
         'Question 5 is completely optional. You can submit with Q1 to Q4 filled, or add your elective suggestions in Q5.',
         '2026-10-29 11:15:00'),
        (student_map['vikram_aditya'], subject_map['CS301'],
         'Extension request for Python Flask Mini-Project Submission', 'Academic Request',
         'Requesting a 2-day extension due to annual college hackathon participation.',
         'In Progress',
         'Admin committee is reviewing request with Prof. Ananya Sen.',
         '2026-11-01 09:20:00')
    ]

    for t in tickets:
        cursor.execute('''
        INSERT INTO help_desk_tickets (user_id, subject_id, title, category, message, status, admin_reply, replied_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', t)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    seed_db()
    print("Database initialized and seeded successfully.")

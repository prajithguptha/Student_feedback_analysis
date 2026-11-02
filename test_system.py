import unittest
import app
from models import get_db

class TestBTechFeedbackSystem(unittest.TestCase):
    def setUp(self):
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()

    def test_01_home_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'B.Tech', res.data)
        self.assertIn(b'Python Programming', res.data)

    def test_02_student_login_and_dashboard(self):
        # Login as student Rahul
        res = self.client.post('/login', data={
            'username': 'rahul_verma',
            'password': 'student123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Rahul Verma', res.data)
        self.assertIn(b'Your Semester Evaluation Subjects', res.data)

    def test_03_student_submit_feedback(self):
        # Login as Vikram Aditya (who hasn't submitted CS304 yet)
        self.client.post('/login', data={
            'username': 'vikram_aditya',
            'password': 'student123'
        }, follow_redirects=True)

        # GET feedback form for CS301 (Python)
        res = self.client.get('/feedback/1')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Curriculum & Concept Coverage', res.data)
        self.assertIn(b'Message Box for Question 1', res.data)
        self.assertIn(b'Optional Question', res.data)

        # POST feedback with 5 questions, all 5 message boxes, Q5 included
        res_post = self.client.post('/feedback/1', data={
            'q1_score': 5,
            'q1_message': 'Great explanation of Python OOP and generators.',
            'q2_score': 5,
            'q2_message': 'Live coding demonstrations were very clear.',
            'q3_score': 4,
            'q3_message': 'Pace was good, handled questions promptly.',
            'q4_score': 5,
            'q4_message': 'Lab problems on Flask web development were hands-on.',
            'q5_score': 5,
            'q5_message': 'Please consider adding a PyTorch module in 6th semester.'
        }, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)
        self.assertIn(b'submitted successfully', res_post.data)

    def test_04_admin_login_and_security(self):
        # Login as Dr. Rajesh (Admin)
        res = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Faculty Executive Dashboard', res.data)
        self.assertIn(b'Recent Student Submissions Log', res.data)

        # Admin can view student feedbacks directory
        res_admin_fb = self.client.get('/admin/feedbacks')
        self.assertEqual(res_admin_fb.status_code, 200)
        self.assertIn(b'Student Feedback Submissions Directory', res_admin_fb.data)
        self.assertIn(b'Rahul Verma', res_admin_fb.data)

        # Admin can export CSV
        res_csv = self.client.get('/admin/export_csv')
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.content_type, 'text/csv; charset=utf-8')
        self.assertIn(b'Q1 Remarks (Message Box)', res_csv.data)

    def test_05_student_cannot_view_admin_feedbacks(self):
        # Login as student
        self.client.post('/login', data={
            'username': 'rahul_verma',
            'password': 'student123'
        }, follow_redirects=True)

        # Attempt to access /admin/feedbacks
        res = self.client.get('/admin/feedbacks', follow_redirects=True)
        # Should be redirected to dashboard with Access denied
        self.assertIn(b'Access denied: Only Administrators can view student feedback details', res.data)

    def test_06_quick_status_api(self):
        self.client.post('/login', data={
            'username': 'rahul_verma',
            'password': 'student123'
        }, follow_redirects=True)
        res = self.client.get('/api/quick-status')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['authenticated'])
        self.assertEqual(data['role'], 'student')
        self.assertTrue(len(data['subjects']) > 0)

if __name__ == '__main__':
    unittest.main()

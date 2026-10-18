import unittest
import os
import json
import io
import csv
from app import app
from database import init_db, get_connection, clear_synthetic_data, format_sql, check_db_health
from config import Config

class TestDiabetesSurveyPortalProduction(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            init_db()

    def test_01_health_check_endpoint(self):
        """Test production /health endpoint returns HTTP 200 and connected status."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('database'), 'connected')

    def test_02_login_page_never_exposes_credentials(self):
        """Verify that login.html does not render default or plaintext credentials."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertNotIn("Admin@CSP2024", html)
        self.assertNotIn("<code>admin</code>", html)
        self.assertIn("Authorized Access Only", html)

    def test_03_home_page(self):
        """Test home landing page accessibility and title."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Diabetes &amp; Chronic Disease", response.data)
        self.assertIn(b"Community Survey Project (CSP)", response.data)

    def test_04_survey_page_loads_and_has_questions(self):
        """Test survey page renders all sections and questions verbatim."""
        response = self.client.get('/survey')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Section 1", response.data)
        self.assertIn(b"Basic Information", response.data)
        self.assertIn(b"Section 2", response.data)
        self.assertIn(b"Awareness of Diabetes", response.data)
        self.assertIn(b"Q1. Name of Respondent (Optional)", response.data)
        self.assertIn(b"Q2. Age", response.data)
        self.assertIn(b"Q3. Gender", response.data)
        self.assertIn(b"Q9. Have you ever been diagnosed with Diabetes?", response.data)
        self.assertIn(b"Q12. How often do you exercise or engage in physical activity?", response.data)
        self.assertIn(b"Q30. In your opinion, what measures can help prevent diabetes", response.data)
        self.assertIn(b"Declaration by Respondent", response.data)

    def test_05_submission_missing_mandatory_fields(self):
        """Test survey rejection when mandatory fields are omitted."""
        incomplete_payload = {
            'q1_full_name': 'Test Respondent',
        }
        response = self.client.post('/survey/submit', data=incomplete_payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Mandatory fields missing", response.data)

    def test_06_successful_survey_submission(self):
        """Test complete and valid survey submission."""
        valid_payload = {
            'location_type': 'Rural',
            'survey_location': 'Ananthapur Ward 3',
            'surveyor_name': 'Tester Surveyor',
            'q1_full_name': 'Confidential Citizen',
            'q2_age_group': '31 – 45 years',
            'q3_gender': 'Female',
            'q4_occupation': 'Farmer / Agricultural Worker',
            'q5_education': 'Secondary School (Class 6–10)',
            'q6_heard_diabetes': 'Yes',
            'q7_aware_chronic_diseases': ['Heart Disease (Hypertension / CVD)', 'Kidney Disease (CKD)'],
            'q8_first_learned_source': 'Doctor / Health Worker',
            'q9_diagnosed_diabetes': 'Yes, Type 2 Diabetes',
            'q10_diagnosed_chronic_diseases': ['High Blood Pressure (Hypertension)'],
            'q11_family_history': ['Yes — Diabetes'],
            'q12_exercise_frequency': '2–3 times per week',
            'q13_daily_activity_level': 'Moderately active (regular movement)',
            'q14_sugary_intake_frequency': 'Occasionally',
            'q15_smoking_status': 'No, never',
            'q16_alcohol_consumption': 'No, I don\'t drink',
            'q17_sleep_hours': '7 – 8 hours (Recommended)',
            'q18_diet_type': 'Vegetarian',
            'q19_fruits_veg_frequency': 'Every day',
            'q20_fast_food_frequency': 'Rarely / Never',
            'q21_routine_health_checkup': 'Once a year',
            'q22_blood_sugar_test_frequency': 'Every 3–6 months',
            'q23_healthcare_accessibility': 'Within 1 km (easily accessible)',
            'q24_medicines_access': 'Yes, always available and affordable',
            'q25_daily_life_impact': 'Yes, mildly affected',
            'q26_monthly_expenditure': '₹501 – ₹2,000',
            'q27_challenges': ['High cost of medicines / treatment'],
            'q28_community_awareness_programs': 'Yes, regularly',
            'q29_community_knowledge_level': 'Somewhat informed',
            'q30_prevention_measures': 'Regular testing camps in village panchayat.',
            'q31_healthcare_suggestions': 'More frequent visits by specialist doctors.',
            'q32_future_participation': 'Yes',
            'consent_given': '1'
        }

        headers = {'X-Forwarded-For': '192.168.1.155'}
        response = self.client.post('/survey/submit', data=valid_payload, headers=headers, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Thank You for Your Valuable Participation!", response.data)
        self.assertIn(b"CSP-", response.data)

    def test_07_admin_authentication_and_protection(self):
        """Test route protection for admin dashboard."""
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

        res = self.client.post('/login', data={'username': 'admin', 'password': 'wrongpassword'}, follow_redirects=True)
        self.assertIn(b"Invalid username or password", res.data)

        res = self.client.post('/login', data={'username': Config.ADMIN_USERNAME, 'password': Config.ADMIN_PASSWORD}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Community Survey Analytics &amp; Statistical Insights", res.data)

    def test_08_dashboard_api_endpoints_and_csv_export(self):
        """Test API stats, response pagination, and anonymized CSV export."""
        self.client.post('/login', data={'username': Config.ADMIN_USERNAME, 'password': Config.ADMIN_PASSWORD})

        stats_res = self.client.get('/api/stats')
        self.assertEqual(stats_res.status_code, 200)
        stats_json = stats_res.get_json()
        self.assertIn('total_n', stats_json)
        self.assertIn('diabetes_prevalence', stats_json)

        resp_res = self.client.get('/api/responses?page=1&per_page=5')
        self.assertEqual(resp_res.status_code, 200)
        resp_json = resp_res.get_json()
        self.assertIn('records', resp_json)

        csv_res = self.client.get('/export/csv')
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.headers['Content-Type'], 'text/csv; charset=utf-8')
        csv_text = csv_res.data.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_text))
        header = next(csv_reader)
        self.assertIn('Response_Reference_ID', header)
        self.assertIn('Q9_Diagnosed_Diabetes', header)
        self.assertNotIn('q1_full_name', header)

    def test_09_production_fail_safe_secrets_validation(self):
        """Verify that Config raises RuntimeError if production secrets are missing or weak."""
        import importlib
        original_env = os.environ.copy()

        try:
            # 1. Missing SECRET_KEY in production
            os.environ['FLASK_ENV'] = 'production'
            os.environ.pop('SECRET_KEY', None)
            with self.assertRaises(RuntimeError) as ctx:
                import config
                importlib.reload(config)
            self.assertIn("SECRET_KEY", str(ctx.exception))

            # 2. Insecure default ADMIN_PASSWORD in production
            os.environ['SECRET_KEY'] = 'a-very-long-production-grade-secret-key-12345'
            os.environ['ADMIN_USERNAME'] = 'researcher_lead'
            os.environ['ADMIN_PASSWORD'] = 'Admin@CSP2024'  # Default password!
            with self.assertRaises(RuntimeError) as ctx:
                import config
                importlib.reload(config)
            self.assertIn("ADMIN_PASSWORD", str(ctx.exception))

            # 3. Valid production configuration succeeds
            os.environ['ADMIN_PASSWORD'] = 'SecureUniquePassphrase2024#%'
            import config
            importlib.reload(config)
            self.assertTrue(config.Config.IS_PRODUCTION)
            self.assertFalse(config.Config.DEBUG)
            self.assertTrue(config.Config.SESSION_COOKIE_SECURE)

        finally:
            os.environ.clear()
            os.environ.update(original_env)
            import config
            importlib.reload(config)

    def test_10_demo_data_gate_in_production(self):
        """Verify that demo data seeder is blocked when ENABLE_DEMO_DATA is False."""
        self.client.post('/login', data={'username': Config.ADMIN_USERNAME, 'password': Config.ADMIN_PASSWORD})

        # Temporarily disable demo data
        original_flag = Config.ENABLE_DEMO_DATA
        try:
            Config.ENABLE_DEMO_DATA = False
            res = self.client.post('/admin/seed-demo', follow_redirects=True)
            self.assertIn(b"disabled in production", res.data)

            res2 = self.client.post('/admin/clear-demo', follow_redirects=True)
            self.assertIn(b"disabled in production", res2.data)
        finally:
            Config.ENABLE_DEMO_DATA = original_flag

    def test_11_sql_placeholder_adapter(self):
        """Verify that format_sql correctly replaces ? with %s when on PostgreSQL."""
        from database import format_sql
        # SQLite mode (default)
        raw_query = "SELECT * FROM survey_responses WHERE id = ? AND reference_id = ?"
        self.assertEqual(format_sql(raw_query), raw_query)

if __name__ == '__main__':
    unittest.main()

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from functools import wraps
import json
import logging
import hmac
from config import Config
from database import (
    init_db,
    save_survey_response,
    get_survey_statistics,
    get_responses_paginated,
    get_response_by_ref,
    export_anonymized_csv,
    clear_synthetic_data,
    check_recent_duplicate,
    check_db_health,
    hash_ip
)
from seed_data import generate_synthetic_surveys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Ensure database tables exist on startup
with app.app_context():
    try:
        init_db()
        logger.info(f"Database initialized successfully (Engine: {'PostgreSQL' if Config.DATABASE_URL else 'SQLite'}).")
    except Exception as e:
        logger.error(f"Failed to initialize database on startup: {e}")

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Administrator authentication required to access this research area.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# HEALTH PROBE ROUTE
# ==========================================

@app.route('/health')
def health_check():
    """
    Production health check probe for Render and uptime monitoring.
    Verifies actual database read/write connectivity.
    """
    is_healthy, message = check_db_health()
    status_code = 200 if is_healthy else 503
    return jsonify({
        "status": "healthy" if is_healthy else "unhealthy",
        "database": "connected" if is_healthy else "disconnected",
        "detail": message,
        "environment": Config.ENV
    }), status_code

# ==========================================
# PUBLIC ROUTES
# ==========================================

@app.route('/')
def home():
    """Home landing page with CSP project mission and live statistics."""
    try:
        stats = get_survey_statistics(include_synthetic=True)
    except Exception as e:
        logger.error(f"Error fetching stats for home: {e}")
        stats = {"total_n": 0, "diabetes_prevalence": 0, "rural_pct": 0, "sedentary_pct": 0}
    return render_template('index.html', stats=stats, active_page='home')

@app.route('/survey')
def survey_page():
    """The authoritative 32-question survey wizard page."""
    return render_template('survey.html', active_page='survey')

@app.route('/survey/submit', methods=['POST'])
def submit_survey():
    """Process and validate submitted survey questionnaire."""
    # Capture respondent IP for anti-spam rate limiting
    ip_addr = request.headers.get('X-Forwarded-For', request.remote_addr or '127.0.0.1')
    if ',' in ip_addr:
        ip_addr = ip_addr.split(',')[0].strip()

    ip_h = hash_ip(ip_addr)
    if check_recent_duplicate(ip_h, window_seconds=8):
        flash('A survey submission was just received from this device. Please wait a few seconds before submitting again.', 'error')
        return redirect(url_for('survey_page'))

    # Extract single and multi-select form data
    form = request.form
    
    # Server-side Mandatory Validation
    mandatory_fields = {
        'q2_age_group': 'Q2 (Age)',
        'q3_gender': 'Q3 (Gender)',
        'q5_education': 'Q5 (Highest Education Level Completed)',
        'q6_heard_diabetes': 'Q6 (Heard about Diabetes)',
        'q8_first_learned_source': 'Q8 (How you first learned)',
        'q9_diagnosed_diabetes': 'Q9 (Diagnosed with Diabetes)',
        'q12_exercise_frequency': 'Q12 (Physical activity frequency)'
    }

    missing_fields = []
    for field_key, field_label in mandatory_fields.items():
        val = form.get(field_key, '').strip()
        if not val:
            missing_fields.append(field_label)

    # Consent verification
    consent_checked = form.get('consent_given')
    if not consent_checked:
        missing_fields.append('Declaration & Informed Consent')

    if missing_fields:
        error_msg = f"Submission rejected. Mandatory fields missing: {', '.join(missing_fields)}"
        flash(error_msg, 'error')
        return redirect(url_for('survey_page'))

    # Prepare data dictionary for database persistence
    data = {
        'location_type': form.get('location_type', 'Rural'),
        'survey_location': form.get('survey_location', '').strip(),
        'surveyor_name': form.get('surveyor_name', '').strip(),
        'q1_full_name': form.get('q1_full_name', '').strip(),
        'q2_age_group': form.get('q2_age_group', '').strip(),
        'q3_gender': form.get('q3_gender', '').strip(),
        'q4_occupation': form.get('q4_occupation', '').strip(),
        'q5_education': form.get('q5_education', '').strip(),
        'q6_heard_diabetes': form.get('q6_heard_diabetes', '').strip(),
        'q7_aware_chronic_diseases': form.getlist('q7_aware_chronic_diseases'),
        'q8_first_learned_source': form.get('q8_first_learned_source', '').strip(),
        'q9_diagnosed_diabetes': form.get('q9_diagnosed_diabetes', '').strip(),
        'q10_diagnosed_chronic_diseases': form.getlist('q10_diagnosed_chronic_diseases'),
        'q11_family_history': form.getlist('q11_family_history'),
        'q12_exercise_frequency': form.get('q12_exercise_frequency', '').strip(),
        'q13_daily_activity_level': form.get('q13_daily_activity_level', '').strip(),
        'q14_sugary_intake_frequency': form.get('q14_sugary_intake_frequency', '').strip(),
        'q15_smoking_status': form.get('q15_smoking_status', '').strip(),
        'q16_alcohol_consumption': form.get('q16_alcohol_consumption', '').strip(),
        'q17_sleep_hours': form.get('q17_sleep_hours', '').strip(),
        'q18_diet_type': form.get('q18_diet_type', '').strip(),
        'q19_fruits_veg_frequency': form.get('q19_fruits_veg_frequency', '').strip(),
        'q20_fast_food_frequency': form.get('q20_fast_food_frequency', '').strip(),
        'q21_routine_health_checkup': form.get('q21_routine_health_checkup', '').strip(),
        'q22_blood_sugar_test_frequency': form.get('q22_blood_sugar_test_frequency', '').strip(),
        'q23_healthcare_accessibility': form.get('q23_healthcare_accessibility', '').strip(),
        'q24_medicines_access': form.get('q24_medicines_access', '').strip(),
        'q25_daily_life_impact': form.get('q25_daily_life_impact', '').strip(),
        'q26_monthly_expenditure': form.get('q26_monthly_expenditure', '').strip(),
        'q27_challenges': form.getlist('q27_challenges'),
        'q28_community_awareness_programs': form.get('q28_community_awareness_programs', '').strip(),
        'q29_community_knowledge_level': form.get('q29_community_knowledge_level', '').strip(),
        'q30_prevention_measures': form.get('q30_prevention_measures', '').strip(),
        'q31_healthcare_suggestions': form.get('q31_healthcare_suggestions', '').strip(),
        'q32_future_participation': form.get('q32_future_participation', '').strip(),
        'consent_given': 1,
        'is_synthetic': 0
    }

    try:
        ref_id = save_survey_response(data, ip_address=ip_addr)
        flash('Survey submitted successfully! Thank you for your valuable contribution.', 'success')
        return redirect(url_for('survey_success', reference_id=ref_id))
    except Exception as e:
        logger.error(f"Error persisting survey response: {e}")
        flash('A database error occurred while saving your responses. Please try again.', 'error')
        return redirect(url_for('survey_page'))

@app.route('/survey/success/<reference_id>')
def survey_success(reference_id):
    """Confirmation page with unique audit reference ID."""
    return render_template('survey_success.html', reference_id=reference_id)

@app.route('/about')
def about_page():
    """About page with academic methodology, ethics, and coordinator demonstration guide."""
    return render_template('about.html', active_page='about')

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Administrator login with constant-time comparison to prevent timing attacks."""
    if session.get('admin_logged_in'):
        return redirect(url_for('dashboard_page'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Constant-time string comparison for credential verification
        user_valid = hmac.compare_digest(username, Config.ADMIN_USERNAME)
        pass_valid = hmac.compare_digest(password, Config.ADMIN_PASSWORD)

        if user_valid and pass_valid:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Logged in successfully as Administrator.', 'success')
            next_url = request.args.get('next') or url_for('dashboard_page')
            return redirect(next_url)
        else:
            flash('Invalid username or password. Please check your credentials.', 'error')

    return render_template('login.html', active_page='login')

@app.route('/logout')
def logout():
    """Administrator logout."""
    session.clear()
    flash('You have been logged out of the administrative portal.', 'info')
    return redirect(url_for('home'))

# ==========================================
# ADMIN DASHBOARD & RESEARCH DATA ROUTES
# ==========================================

@app.route('/dashboard')
@admin_required
def dashboard_page():
    """Admin analytics and research dashboard."""
    try:
        stats = get_survey_statistics(include_synthetic=True)
    except Exception as e:
        logger.error(f"Error loading dashboard statistics: {e}")
        stats = get_survey_statistics(include_synthetic=False)
    return render_template('dashboard.html', stats=stats, active_page='dashboard')

@app.route('/api/stats')
@admin_required
def api_stats():
    """JSON API endpoint returning live statistical aggregates."""
    include_synthetic = request.args.get('synthetic', 'true').lower() == 'true'
    stats = get_survey_statistics(include_synthetic=include_synthetic)
    return jsonify(stats)

@app.route('/api/responses')
@admin_required
def api_responses():
    """Paginated JSON endpoint for the response explorer table."""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    search = request.args.get('search', '').strip()
    location_filter = request.args.get('location', '').strip()
    diabetes_filter = request.args.get('diabetes', '').strip()

    data = get_responses_paginated(
        page=page,
        per_page=per_page,
        search=search,
        location_filter=location_filter,
        diabetes_filter=diabetes_filter
    )
    return jsonify(data)

@app.route('/api/responses/<reference_id>')
@admin_required
def api_response_detail(reference_id):
    """Single response inspector endpoint."""
    response = get_response_by_ref(reference_id)
    if not response:
        return jsonify({'error': 'Survey response record not found'}), 404
    return jsonify(response)

@app.route('/export/csv')
@admin_required
def export_csv():
    """Export fully anonymized survey responses as a CSV download."""
    csv_content = export_anonymized_csv()
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=CSP_Diabetes_Community_Survey_Anonymized.csv"}
    )

@app.route('/admin/seed-demo', methods=['POST'])
@admin_required
def seed_demo():
    """Seed 50 realistic synthetic demonstration records (disabled in production)."""
    if not Config.ENABLE_DEMO_DATA:
        flash("Demonstration data generation is disabled in production to protect data integrity.", "error")
        return redirect(url_for('dashboard_page'))

    count = generate_synthetic_surveys(50)
    flash(f"Successfully generated {count} realistic demonstration records (flagged as synthetic).", 'success')
    return redirect(url_for('dashboard_page'))

@app.route('/admin/clear-demo', methods=['POST'])
@admin_required
def clear_demo():
    """Remove synthetic demonstration records (disabled in production)."""
    if not Config.ENABLE_DEMO_DATA:
        flash("Demonstration data clearing is disabled in production.", "error")
        return redirect(url_for('dashboard_page'))

    removed = clear_synthetic_data()
    flash(f"Removed {removed} synthetic records. Only genuine survey responses are now retained.", 'info')
    return redirect(url_for('dashboard_page'))

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found(e):
    return render_template('base.html', content='<div class="container" style="padding:4rem; text-align:center;"><h2>Page Not Found (404)</h2><p>The requested page could not be located.</p><a href="/" class="btn btn-primary" style="margin-top:1rem;">Back to Home</a></div>'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', content='<div class="container" style="padding:4rem; text-align:center;"><h2>Internal Server Error (500)</h2><p>An unexpected error occurred. Please try again later.</p><a href="/" class="btn btn-primary" style="margin-top:1rem;">Back to Home</a></div>'), 500

if __name__ == '__main__':
    logger.info(f"Starting Diabetes & Chronic Disease Community Survey Portal on http://{Config.HOST}:{Config.PORT} (Debug={Config.DEBUG})")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)

import sqlite3
import json
import uuid
import hashlib
import os
import csv
import io
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

def is_postgres():
    """Return True if PostgreSQL DATABASE_URL is configured."""
    return bool(Config.DATABASE_URL)

def get_connection():
    """
    Create and return a database connection.
    Connects to PostgreSQL if DATABASE_URL is configured, else SQLite.
    """
    if is_postgres():
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def format_sql(query):
    """Adapt SQL placeholder syntax (? for SQLite, %s for PostgreSQL)."""
    if is_postgres():
        return query.replace('?', '%s')
    return query

def check_db_health():
    """Verify database connectivity for production health probes."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        res = cursor.fetchone()
        return True, "Database connection operational"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False, str(e)
    finally:
        if conn:
            conn.close()

def init_db():
    """Initialize database tables and indexes on SQLite or PostgreSQL."""
    conn = get_connection()
    cursor = conn.cursor()

    pg = is_postgres()
    id_type = "SERIAL PRIMARY KEY" if pg else "INTEGER PRIMARY KEY AUTOINCREMENT"

    # Survey Responses table
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS survey_responses (
        id {id_type},
        reference_id VARCHAR(36) UNIQUE NOT NULL,
        location_type VARCHAR(30) NOT NULL,
        survey_location VARCHAR(100),
        surveyor_name VARCHAR(100),
        q1_full_name VARCHAR(100),
        q2_age_group VARCHAR(30) NOT NULL,
        q3_gender VARCHAR(30) NOT NULL,
        q4_occupation VARCHAR(50),
        q5_education VARCHAR(50) NOT NULL,
        q6_heard_diabetes VARCHAR(10) NOT NULL,
        q7_aware_chronic_diseases TEXT,
        q8_first_learned_source VARCHAR(60) NOT NULL,
        q9_diagnosed_diabetes VARCHAR(40) NOT NULL,
        q10_diagnosed_chronic_diseases TEXT,
        q11_family_history TEXT,
        q12_exercise_frequency VARCHAR(40) NOT NULL,
        q13_daily_activity_level VARCHAR(40),
        q14_sugary_intake_frequency VARCHAR(30),
        q15_smoking_status VARCHAR(30),
        q16_alcohol_consumption VARCHAR(40),
        q17_sleep_hours VARCHAR(30),
        q18_diet_type VARCHAR(40),
        q19_fruits_veg_frequency VARCHAR(30),
        q20_fast_food_frequency VARCHAR(30),
        q21_routine_health_checkup VARCHAR(30),
        q22_blood_sugar_test_frequency VARCHAR(40),
        q23_healthcare_accessibility VARCHAR(50),
        q24_medicines_access VARCHAR(50),
        q25_daily_life_impact VARCHAR(40),
        q26_monthly_expenditure VARCHAR(50),
        q27_challenges TEXT,
        q28_community_awareness_programs VARCHAR(30),
        q29_community_knowledge_level VARCHAR(30),
        q30_prevention_measures TEXT,
        q31_healthcare_suggestions TEXT,
        q32_future_participation VARCHAR(30),
        consent_given INTEGER NOT NULL DEFAULT 1,
        is_synthetic INTEGER NOT NULL DEFAULT 0,
        ip_hash VARCHAR(64),
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_diagnosed_diabetes ON survey_responses(q9_diagnosed_diabetes);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_location_type ON survey_responses(location_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_age_group ON survey_responses(q2_age_group);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_submitted_at ON survey_responses(submitted_at);")

    # Admin users table
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS admin_users (
        id {id_type},
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

def hash_ip(ip_address):
    """Securely hash respondent IP with salt for rate-limiting without storing raw IP."""
    salt = Config.SECRET_KEY[:16]
    return hashlib.sha256((str(ip_address) + salt).encode('utf-8')).hexdigest()

def check_recent_duplicate(ip_hash, window_seconds=10):
    """Check if same IP submitted within a very short window to avoid double-clicking."""
    conn = get_connection()
    cursor = conn.cursor()

    if is_postgres():
        sql = """
            SELECT COUNT(*) as count FROM survey_responses
            WHERE ip_hash = %s AND (EXTRACT(EPOCH FROM NOW()) - EXTRACT(EPOCH FROM submitted_at)) < %s
        """
        cursor.execute(sql, (ip_hash, window_seconds))
    else:
        sql = """
            SELECT COUNT(*) as count FROM survey_responses
            WHERE ip_hash = ? AND (strftime('%s', 'now') - strftime('%s', submitted_at)) < ?
        """
        cursor.execute(sql, (ip_hash, window_seconds))

    row = cursor.fetchone()
    count = row['count'] if row else 0
    conn.close()
    return count > 0

def save_survey_response(data, ip_address=""):
    """Save a validated survey response using safe parameterized query."""
    conn = get_connection()
    cursor = conn.cursor()

    ref_id = f"CSP-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
    ip_h = hash_ip(ip_address) if ip_address else ""

    q7_json = json.dumps(data.get('q7_aware_chronic_diseases', [])) if isinstance(data.get('q7_aware_chronic_diseases'), list) else str(data.get('q7_aware_chronic_diseases', '[]'))
    q10_json = json.dumps(data.get('q10_diagnosed_chronic_diseases', [])) if isinstance(data.get('q10_diagnosed_chronic_diseases'), list) else str(data.get('q10_diagnosed_chronic_diseases', '[]'))
    q11_json = json.dumps(data.get('q11_family_history', [])) if isinstance(data.get('q11_family_history'), list) else str(data.get('q11_family_history', '[]'))
    q27_json = json.dumps(data.get('q27_challenges', [])) if isinstance(data.get('q27_challenges'), list) else str(data.get('q27_challenges', '[]'))

    sql = """
        INSERT INTO survey_responses (
            reference_id, location_type, survey_location, surveyor_name,
            q1_full_name, q2_age_group, q3_gender, q4_occupation, q5_education,
            q6_heard_diabetes, q7_aware_chronic_diseases, q8_first_learned_source,
            q9_diagnosed_diabetes, q10_diagnosed_chronic_diseases, q11_family_history,
            q12_exercise_frequency, q13_daily_activity_level, q14_sugary_intake_frequency,
            q15_smoking_status, q16_alcohol_consumption, q17_sleep_hours,
            q18_diet_type, q19_fruits_veg_frequency, q20_fast_food_frequency,
            q21_routine_health_checkup, q22_blood_sugar_test_frequency,
            q23_healthcare_accessibility, q24_medicines_access,
            q25_daily_life_impact, q26_monthly_expenditure, q27_challenges,
            q28_community_awareness_programs, q29_community_knowledge_level,
            q30_prevention_measures, q31_healthcare_suggestions, q32_future_participation,
            consent_given, is_synthetic, ip_hash
        ) VALUES (
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?, ?
        )
    """

    params = (
        ref_id,
        data.get('location_type', 'Rural'),
        data.get('survey_location', '').strip(),
        data.get('surveyor_name', '').strip(),
        data.get('q1_full_name', '').strip(),
        data.get('q2_age_group', ''),
        data.get('q3_gender', ''),
        data.get('q4_occupation', ''),
        data.get('q5_education', ''),
        data.get('q6_heard_diabetes', ''),
        q7_json,
        data.get('q8_first_learned_source', ''),
        data.get('q9_diagnosed_diabetes', ''),
        q10_json,
        q11_json,
        data.get('q12_exercise_frequency', ''),
        data.get('q13_daily_activity_level', ''),
        data.get('q14_sugary_intake_frequency', ''),
        data.get('q15_smoking_status', ''),
        data.get('q16_alcohol_consumption', ''),
        data.get('q17_sleep_hours', ''),
        data.get('q18_diet_type', ''),
        data.get('q19_fruits_veg_frequency', ''),
        data.get('q20_fast_food_frequency', ''),
        data.get('q21_routine_health_checkup', ''),
        data.get('q22_blood_sugar_test_frequency', ''),
        data.get('q23_healthcare_accessibility', ''),
        data.get('q24_medicines_access', ''),
        data.get('q25_daily_life_impact', ''),
        data.get('q26_monthly_expenditure', ''),
        q27_json,
        data.get('q28_community_awareness_programs', ''),
        data.get('q29_community_knowledge_level', ''),
        data.get('q30_prevention_measures', '').strip(),
        data.get('q31_healthcare_suggestions', '').strip(),
        data.get('q32_future_participation', ''),
        1 if data.get('consent_given') else 0,
        1 if data.get('is_synthetic') else 0,
        ip_h
    )

    cursor.execute(format_sql(sql), params)
    conn.commit()
    conn.close()
    return ref_id

def get_survey_statistics(include_synthetic=True):
    """
    Compute comprehensive statistical insights and distributions.
    All percentages are explicitly calculated against defined denominators (total N).
    """
    conn = get_connection()
    cursor = conn.cursor()

    synth_clause = "" if include_synthetic else "WHERE is_synthetic = 0"

    # Total responses
    cursor.execute(format_sql(f"SELECT COUNT(*) as total FROM survey_responses {synth_clause}"))
    total_n = cursor.fetchone()['total']

    # Total genuine vs synthetic
    cursor.execute(format_sql("SELECT is_synthetic, COUNT(*) as cnt FROM survey_responses GROUP BY is_synthetic"))
    synth_counts = {row['is_synthetic']: row['cnt'] for row in cursor.fetchall()}
    genuine_n = synth_counts.get(0, 0)
    synthetic_n = synth_counts.get(1, 0)

    if total_n == 0:
        conn.close()
        return {
            "total_n": 0,
            "genuine_n": 0,
            "synthetic_n": 0,
            "diabetes_prevalence": 0,
            "hypertension_prevalence": 0,
            "rural_pct": 0,
            "urban_pct": 0,
            "sedentary_pct": 0,
            "diabetes_distribution": {},
            "age_distribution": {},
            "gender_distribution": {},
            "location_distribution": {},
            "chronic_diseases_frequency": {},
            "family_history_frequency": {},
            "exercise_distribution": {},
            "sugary_intake_distribution": {},
            "blood_sugar_test_frequency": {},
            "healthcare_access_distribution": {},
            "expenditure_distribution": {},
            "challenges_frequency": {},
            "cross_age_diabetes": {},
            "cross_activity_diabetes": {}
        }

    # Diabetes Diagnosis distribution (Q9)
    cursor.execute(format_sql(f"""
        SELECT q9_diagnosed_diabetes, COUNT(*) as cnt
        FROM survey_responses {synth_clause}
        GROUP BY q9_diagnosed_diabetes
    """))
    diabetes_dist = {row['q9_diagnosed_diabetes']: row['cnt'] for row in cursor.fetchall()}

    diagnosed_diab_count = sum(
        cnt for key, cnt in diabetes_dist.items()
        if "Yes" in key
    )
    diab_prevalence = round((diagnosed_diab_count / total_n) * 100, 1)

    # Location distribution
    cursor.execute(format_sql(f"""
        SELECT location_type, COUNT(*) as cnt
        FROM survey_responses {synth_clause}
        GROUP BY location_type
    """))
    loc_dist = {row['location_type']: row['cnt'] for row in cursor.fetchall()}
    rural_pct = round((loc_dist.get('Rural', 0) / total_n) * 100, 1)
    urban_pct = round((loc_dist.get('Urban', 0) / total_n) * 100, 1)

    # Age distribution
    cursor.execute(format_sql(f"""
        SELECT q2_age_group, COUNT(*) as cnt
        FROM survey_responses {synth_clause}
        GROUP BY q2_age_group
    """))
    age_dist = {row['q2_age_group']: row['cnt'] for row in cursor.fetchall()}

    # Gender distribution
    cursor.execute(format_sql(f"""
        SELECT q3_gender, COUNT(*) as cnt
        FROM survey_responses {synth_clause}
        GROUP BY q3_gender
    """))
    gender_dist = {row['q3_gender']: row['cnt'] for row in cursor.fetchall()}

    # Exercise frequency
    cursor.execute(format_sql(f"""
        SELECT q12_exercise_frequency, COUNT(*) as cnt
        FROM survey_responses {synth_clause}
        GROUP BY q12_exercise_frequency
    """))
    exercise_dist = {row['q12_exercise_frequency']: row['cnt'] for row in cursor.fetchall()}

    # Sedentary activity level
    cursor.execute(format_sql(f"""
        SELECT q13_daily_activity_level, COUNT(*) as cnt
        FROM survey_responses {synth_clause}
        GROUP BY q13_daily_activity_level
    """))
    activity_dist = {row['q13_daily_activity_level']: row['cnt'] for row in cursor.fetchall()}
    sedentary_count = activity_dist.get('Sedentary (mostly sitting)', 0)
    sedentary_pct = round((sedentary_count / total_n) * 100, 1)

    # Sugary foods intake
    cursor.execute(format_sql(f"""
        SELECT q14_sugary_intake_frequency, COUNT(*) as cnt
        FROM survey_responses {synth_clause}
        GROUP BY q14_sugary_intake_frequency
    """))
    sugary_dist = {row['q14_sugary_intake_frequency']: row['cnt'] for row in cursor.fetchall() if row['q14_sugary_intake_frequency']}

    # Blood sugar test frequency
    cursor.execute(format_sql(f"""
        SELECT q22_blood_sugar_test_frequency, COUNT(*) as cnt
        FROM survey_responses {synth_clause}
        GROUP BY q22_blood_sugar_test_frequency
    """))
    blood_sugar_dist = {row['q22_blood_sugar_test_frequency']: row['cnt'] for row in cursor.fetchall() if row['q22_blood_sugar_test_frequency']}

    # Healthcare facility accessibility
    cursor.execute(format_sql(f"""
        SELECT q23_healthcare_accessibility, COUNT(*) as cnt
        FROM survey_responses {synth_clause}
        GROUP BY q23_healthcare_accessibility
    """))
    access_dist = {row['q23_healthcare_accessibility']: row['cnt'] for row in cursor.fetchall() if row['q23_healthcare_accessibility']}

    # Monthly expenditure
    cursor.execute(format_sql(f"""
        SELECT q26_monthly_expenditure, COUNT(*) as cnt
        FROM survey_responses {synth_clause}
        GROUP BY q26_monthly_expenditure
    """))
    expend_dist = {row['q26_monthly_expenditure']: row['cnt'] for row in cursor.fetchall() if row['q26_monthly_expenditure']}

    # Q10 Diagnosed chronic diseases unpacking
    cursor.execute(format_sql(f"SELECT q10_diagnosed_chronic_diseases FROM survey_responses {synth_clause}"))
    chronic_freq = {}
    hypertension_count = 0
    for row in cursor.fetchall():
        val = row['q10_diagnosed_chronic_diseases']
        if val:
            try:
                items = json.loads(val)
                if isinstance(items, list):
                    for item in items:
                        clean_item = item.strip()
                        if clean_item and clean_item != "No chronic disease diagnosed":
                            chronic_freq[clean_item] = chronic_freq.get(clean_item, 0) + 1
                            if "Hypertension" in clean_item or "Blood Pressure" in clean_item:
                                hypertension_count += 1
            except Exception:
                pass
    hypertension_pct = round((hypertension_count / total_n) * 100, 1)

    # Q11 Family history unpacking
    cursor.execute(format_sql(f"SELECT q11_family_history FROM survey_responses {synth_clause}"))
    fam_hist_freq = {}
    for row in cursor.fetchall():
        val = row['q11_family_history']
        if val:
            try:
                items = json.loads(val)
                if isinstance(items, list):
                    for item in items:
                        clean_item = item.strip()
                        if clean_item and "No family history" not in clean_item and "Not aware" not in clean_item:
                            fam_hist_freq[clean_item] = fam_hist_freq.get(clean_item, 0) + 1
            except Exception:
                pass

    # Q27 Challenges unpacking
    cursor.execute(format_sql(f"SELECT q27_challenges FROM survey_responses {synth_clause}"))
    challenges_freq = {}
    for row in cursor.fetchall():
        val = row['q27_challenges']
        if val:
            try:
                items = json.loads(val)
                if isinstance(items, list):
                    for item in items:
                        clean_item = item.strip()
                        if clean_item and clean_item != "No major challenges":
                            challenges_freq[clean_item] = challenges_freq.get(clean_item, 0) + 1
            except Exception:
                pass

    # Cross-tabulation: Age group vs Diagnosed Diabetes
    cursor.execute(format_sql(f"""
        SELECT q2_age_group,
               SUM(CASE WHEN q9_diagnosed_diabetes IN ('Yes, Type 1 Diabetes', 'Yes, Type 2 Diabetes', 'Yes, but type not known') THEN 1 ELSE 0 END) as diab_yes,
               COUNT(*) as group_total
        FROM survey_responses {synth_clause}
        GROUP BY q2_age_group
    """))
    cross_age_diabetes = {}
    for row in cursor.fetchall():
        grp = row['q2_age_group']
        total_grp = row['group_total']
        yes_grp = row['diab_yes']
        pct = round((yes_grp / total_grp) * 100, 1) if total_grp > 0 else 0
        cross_age_diabetes[grp] = {"diagnosed": yes_grp, "total": total_grp, "percentage": pct}

    # Cross-tabulation: Physical activity level vs Diagnosed Diabetes
    cursor.execute(format_sql(f"""
        SELECT q13_daily_activity_level,
               SUM(CASE WHEN q9_diagnosed_diabetes IN ('Yes, Type 1 Diabetes', 'Yes, Type 2 Diabetes', 'Yes, but type not known') THEN 1 ELSE 0 END) as diab_yes,
               COUNT(*) as group_total
        FROM survey_responses {synth_clause}
        GROUP BY q13_daily_activity_level
    """))
    cross_act_diabetes = {}
    for row in cursor.fetchall():
        lvl = row['q13_daily_activity_level'] or 'Not Specified'
        total_lvl = row['group_total']
        yes_lvl = row['diab_yes']
        pct = round((yes_lvl / total_lvl) * 100, 1) if total_lvl > 0 else 0
        cross_act_diabetes[lvl] = {"diagnosed": yes_lvl, "total": total_lvl, "percentage": pct}

    conn.close()

    return {
        "total_n": total_n,
        "genuine_n": genuine_n,
        "synthetic_n": synthetic_n,
        "diabetes_prevalence": diab_prevalence,
        "hypertension_prevalence": hypertension_pct,
        "rural_pct": rural_pct,
        "urban_pct": urban_pct,
        "sedentary_pct": sedentary_pct,
        "diabetes_distribution": diabetes_dist,
        "age_distribution": age_dist,
        "gender_distribution": gender_dist,
        "location_distribution": loc_dist,
        "chronic_diseases_frequency": chronic_freq,
        "family_history_frequency": fam_hist_freq,
        "exercise_distribution": exercise_dist,
        "sugary_intake_distribution": sugary_dist,
        "blood_sugar_test_frequency": blood_sugar_dist,
        "healthcare_access_distribution": access_dist,
        "expenditure_distribution": expend_dist,
        "challenges_frequency": challenges_freq,
        "cross_age_diabetes": cross_age_diabetes,
        "cross_activity_diabetes": cross_act_diabetes
    }

def get_responses_paginated(page=1, per_page=15, search="", location_filter="", diabetes_filter=""):
    """Get paginated anonymized responses for the admin data table."""
    conn = get_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if search:
        conditions.append("(reference_id LIKE ? OR survey_location LIKE ? OR surveyor_name LIKE ?)")
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])

    if location_filter:
        conditions.append("location_type = ?")
        params.append(location_filter)

    if diabetes_filter:
        if diabetes_filter == "diagnosed":
            conditions.append("q9_diagnosed_diabetes IN ('Yes, Type 1 Diabetes', 'Yes, Type 2 Diabetes', 'Yes, but type not known')")
        elif diabetes_filter == "not_diagnosed":
            conditions.append("q9_diagnosed_diabetes = 'No'")
        elif diabetes_filter == "not_tested":
            conditions.append("q9_diagnosed_diabetes = 'Not tested yet'")

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    cursor.execute(format_sql(f"SELECT COUNT(*) as total FROM survey_responses {where_clause}"), params)
    total_records = cursor.fetchone()['total']

    offset = (page - 1) * per_page
    query_sql = f"""
        SELECT id, reference_id, location_type, survey_location,
               q2_age_group, q3_gender, q5_education, q9_diagnosed_diabetes,
               q10_diagnosed_chronic_diseases, q12_exercise_frequency,
               is_synthetic, submitted_at
        FROM survey_responses
        {where_clause}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """
    cursor.execute(format_sql(query_sql), params + [per_page, offset])

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    total_pages = max(1, (total_records + per_page - 1) // per_page)
    return {
        "records": rows,
        "total": total_records,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }

def get_response_by_ref(reference_id):
    """Retrieve complete response detail by reference ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(format_sql("SELECT * FROM survey_responses WHERE reference_id = ?"), (reference_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for k in ['q7_aware_chronic_diseases', 'q10_diagnosed_chronic_diseases', 'q11_family_history', 'q27_challenges']:
        if d.get(k):
            try:
                d[k] = json.loads(d[k])
            except Exception:
                d[k] = []
        else:
            d[k] = []
    if d.get('q1_full_name'):
        d['q1_full_name_masked'] = d['q1_full_name'][0] + '***' if len(d['q1_full_name']) > 1 else '***'
    else:
        d['q1_full_name_masked'] = 'Anonymous'
    return d

def export_anonymized_csv():
    """
    Generate anonymized CSV in memory.
    Strictly omits q1_full_name and raw IP addresses to protect respondent privacy.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(format_sql("""
        SELECT reference_id, location_type, survey_location,
               q2_age_group, q3_gender, q4_occupation, q5_education,
               q6_heard_diabetes, q7_aware_chronic_diseases, q8_first_learned_source,
               q9_diagnosed_diabetes, q10_diagnosed_chronic_diseases, q11_family_history,
               q12_exercise_frequency, q13_daily_activity_level, q14_sugary_intake_frequency,
               q15_smoking_status, q16_alcohol_consumption, q17_sleep_hours,
               q18_diet_type, q19_fruits_veg_frequency, q20_fast_food_frequency,
               q21_routine_health_checkup, q22_blood_sugar_test_frequency,
               q23_healthcare_accessibility, q24_medicines_access,
               q25_daily_life_impact, q26_monthly_expenditure, q27_challenges,
               q28_community_awareness_programs, q29_community_knowledge_level,
               q30_prevention_measures, q31_healthcare_suggestions, q32_future_participation,
               is_synthetic, submitted_at
        FROM survey_responses
        ORDER BY id ASC
    """))
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    header = [
        "Response_Reference_ID", "Location_Type", "Survey_Area_Ward",
        "Q2_Age_Group", "Q3_Gender", "Q4_Occupation", "Q5_Education_Level",
        "Q6_Heard_Diabetes", "Q7_Aware_Chronic_Diseases", "Q8_First_Learned_Source",
        "Q9_Diagnosed_Diabetes", "Q10_Diagnosed_Chronic_Diseases", "Q11_Family_History",
        "Q12_Physical_Activity_Frequency", "Q13_Daily_Activity_Level", "Q14_Sugary_Intake_Frequency",
        "Q15_Smoking_Status", "Q16_Alcohol_Consumption", "Q17_Average_Sleep_Hours",
        "Q18_Diet_Type", "Q19_Fruits_Veg_Frequency", "Q20_Fast_Food_Frequency",
        "Q21_Routine_Health_Checkup", "Q22_Blood_Sugar_Test_Frequency",
        "Q23_Healthcare_Facility_Distance", "Q24_Medicine_Accessibility",
        "Q25_Daily_Life_Impact", "Q26_Monthly_Treatment_Expenditure_INR", "Q27_Management_Challenges",
        "Q28_Community_Awareness_Programs", "Q29_Community_Knowledge_Rating",
        "Q30_Community_Prevention_Measures", "Q31_Healthcare_Suggestions", "Q32_Future_Participation_Willingness",
        "Is_Synthetic_Demo_Data", "Timestamp_Submitted"
    ]
    writer.writerow(header)

    for r in rows:
        writer.writerow([
            r['reference_id'], r['location_type'], r['survey_location'],
            r['q2_age_group'], r['q3_gender'], r['q4_occupation'], r['q5_education'],
            r['q6_heard_diabetes'], r['q7_aware_chronic_diseases'], r['q8_first_learned_source'],
            r['q9_diagnosed_diabetes'], r['q10_diagnosed_chronic_diseases'], r['q11_family_history'],
            r['q12_exercise_frequency'], r['q13_daily_activity_level'], r['q14_sugary_intake_frequency'],
            r['q15_smoking_status'], r['q16_alcohol_consumption'], r['q17_sleep_hours'],
            r['q18_diet_type'], r['q19_fruits_veg_frequency'], r['q20_fast_food_frequency'],
            r['q21_routine_health_checkup'], r['q22_blood_sugar_test_frequency'],
            r['q23_healthcare_accessibility'], r['q24_medicines_access'],
            r['q25_daily_life_impact'], r['q26_monthly_expenditure'], r['q27_challenges'],
            r['q28_community_awareness_programs'], r['q29_community_knowledge_level'],
            r['q30_prevention_measures'], r['q31_healthcare_suggestions'], r['q32_future_participation'],
            "SYNTHETIC" if r['is_synthetic'] else "GENUINE",
            r['submitted_at']
        ])

    output.seek(0)
    return output.getvalue()

def clear_synthetic_data():
    """Clear synthetic records from database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(format_sql("DELETE FROM survey_responses WHERE is_synthetic = 1"))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected

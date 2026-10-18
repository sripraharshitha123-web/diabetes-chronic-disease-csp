import random
import json
from database import get_connection, hash_ip, format_sql

LOCATIONS = [
    ("Rural", ["Ananthapur Rural Ward 4", "Kallur Village", "Chitradurga Gram Panchayat", "Peddapuram Hamlet", "Rampur Village"]),
    ("Urban", ["Sector 9 Urban Health Area", "Ward 14 Gandhi Nagar", "Indira Nagar Block B", "Subhash Colony Ward 22"]),
    ("Semi-Urban", ["Town Center PHC Circle", "Market Yard Ward 7", "Bypass Road Colony", "Railway Colony Ward 11"])
]

AGE_GROUPS = [
    ("Below 18 years", 0.05),
    ("18 – 30 years", 0.25),
    ("31 – 45 years", 0.30),
    ("46 – 60 years", 0.25),
    ("Above 60 years", 0.15)
]

GENDERS = ["Male", "Female", "Other / Prefer not to say"]
OCCUPATIONS = [
    "Student", "Farmer / Agricultural Worker", "Government Employee",
    "Private Sector Employee", "Self-Employed / Business", "Homemaker", "Retired", "Unemployed"
]

EDUCATIONS = [
    "No formal education", "Primary School (up to Class 5)", "Secondary School (Class 6–10)",
    "Higher Secondary / Intermediate", "Graduate (Degree)", "Post-Graduate or Higher"
]

SOURCES = [
    "Doctor / Health Worker", "Television / Radio", "Internet / Social Media",
    "Newspaper / Magazines", "Family / Friends", "School / College",
    "Health Camp / Awareness Programme", "Never heard / Not aware"
]

CHRONIC_LIST = [
    "High Blood Pressure (Hypertension)", "Heart Disease", "Kidney Disease",
    "Asthma / Breathing Problem", "Thyroid Problem", "Cancer", "Obesity"
]

FAMILY_HIST_LIST = [
    "Yes — Diabetes", "Yes — Heart Disease", "Yes — Cancer", "Yes — Other Chronic Disease"
]

EXERCISE_FREQ = [
    "Daily (≥ 30 minutes)", "4–6 times per week", "2–3 times per week", "Once a week", "Rarely", "Never"
]

DAILY_ACTIVITY = [
    "Sedentary (mostly sitting)", "Lightly active (some walking)",
    "Moderately active (regular movement)", "Very active (physical labour / sport)"
]

SUGARY_FREQ = [
    "Multiple times a day", "Once daily", "3–5 times per week", "Occasionally", "Rarely / Never"
]

SMOKING_STATUS = [
    "Yes, daily", "Yes, occasionally", "I quit smoking", "No, never"
]

ALCOHOL_STATUS = [
    "Yes, daily", "Yes, occasionally (weekends)", "Rarely", "No, I don't drink"
]

SLEEP_HOURS = [
    "Less than 5 hours", "5 – 6 hours", "7 – 8 hours (Recommended)", "More than 8 hours"
]

DIET_TYPES = ["Vegetarian", "Non-Vegetarian", "Mixed (Both Veg & Non-Veg)", "Vegan"]
FRUITS_VEG_FREQ = ["Every day", "4–5 times per week", "2–3 times per week", "Once a week", "Rarely / Never"]
FAST_FOOD_FREQ = ["Daily", "3–5 times per week", "Once or twice a week", "Occasionally", "Rarely / Never"]
ROUTINE_CHECKUP = ["Every 6 months", "Once a year", "Every 2–3 years", "Only when unwell", "Never"]
BLOOD_SUGAR_TEST = ["Monthly", "Every 3–6 months", "Annually", "Only on doctor's advice", "Never tested"]
HEALTHCARE_ACCESS = [
    "Within 1 km (easily accessible)", "1 – 5 km (moderately accessible)",
    "5 – 15 km (difficult to reach)", "More than 15 km (very difficult)"
]
MEDICINES_ACCESS = [
    "Yes, always available and affordable", "Yes, available but expensive",
    "Irregular supply / sometimes available", "No, difficult to access", "Not applicable"
]
DAILY_IMPACT = [
    "Yes, severely affected", "Yes, mildly affected", "Not significantly affected", "No, not affected", "Not applicable (not diagnosed)"
]
EXPENDITURE = [
    "₹0 (No cost / Government supply)", "₹1 – ₹500", "₹501 – ₹2,000", "₹2,001 – ₹5,000", "More than ₹5,000"
]
CHALLENGES = [
    "High cost of medicines / treatment", "Lack of nearby healthcare facilities",
    "Lack of awareness / information", "Busy lifestyle / No time",
    "Side effects of medicines", "Difficulty following diet restrictions"
]
AWARENESS_PROGRAMS = ["Yes, regularly", "Yes, but rarely", "No, never", "Not aware of any"]
COMMUNITY_KNOWLEDGE = ["Yes, very well informed", "Somewhat informed", "Poorly informed", "Not informed at all"]
FUTURE_PARTICIPATION = ["Yes", "No", "Not Sure / Maybe"]

PREVENTION_IDEAS = [
    "Free community health screening camps and sugar testing every month.",
    "Door-to-door counseling on nutrition, low salt, and reduced sugar intake.",
    "Subsidized medicines at the local primary health center (PHC).",
    "Setting up walking tracks, open gyms, and community yoga sessions in villages.",
    "More awareness sessions in local schools and public gatherings about chronic symptoms.",
    "Affordable testing kits and continuous supply of insulin in government clinics."
]

HEALTHCARE_IDEAS = [
    "Ensure doctors are available at the primary health center around the clock.",
    "Stock essential testing strips and chronic disease drugs permanently.",
    "Provide mobile clinic vans to visit remote rural hamlets weekly.",
    "Reduce waiting times and simplify appointment scheduling at district hospitals.",
    "Organize specialized doctor visits for cardiology and endocrinology twice a month."
]

SURVEYORS = ["Surveyor A. Kumar", "Surveyor P. Lakshmi", "Surveyor R. Sharma", "Surveyor M. Fatima"]

def weighted_choice(items_weights):
    items, weights = zip(*items_weights)
    return random.choices(items, weights=weights, k=1)[0]

def generate_synthetic_surveys(count=50):
    conn = get_connection()
    cursor = conn.cursor()

    for i in range(count):
        loc_type, locations = random.choice(LOCATIONS)
        survey_loc = random.choice(locations)
        surveyor = random.choice(SURVEYORS)
        
        age_group = weighted_choice(AGE_GROUPS)
        gender = random.choice(GENDERS)
        occupation = random.choice(OCCUPATIONS)
        education = random.choice(EDUCATIONS)
        
        heard_diab = "Yes" if random.random() > 0.08 else "No"
        aware_diseases = random.sample(CHRONIC_LIST, k=random.randint(1, 4)) if heard_diab == "Yes" else []
        learned_source = random.choice(SOURCES[:-1]) if heard_diab == "Yes" else "Never heard / Not aware"

        # Realistic clinical age correlation for diabetes
        if age_group == "Below 18 years":
            diab_prob = 0.04
        elif age_group == "18 – 30 years":
            diab_prob = 0.08
        elif age_group == "31 – 45 years":
            diab_prob = 0.22
        elif age_group == "46 – 60 years":
            diab_prob = 0.36
        else: # Above 60 years
            diab_prob = 0.44

        r_val = random.random()
        if r_val < diab_prob:
            q9_diab = random.choices(
                ["Yes, Type 2 Diabetes", "Yes, Type 1 Diabetes", "Yes, but type not known"],
                weights=[0.80, 0.10, 0.10], k=1
            )[0]
        elif r_val < diab_prob + 0.12:
            q9_diab = "Not tested yet"
        else:
            q9_diab = "No"

        # Other chronic conditions
        if "Yes" in q9_diab:
            diag_chronic = random.sample(CHRONIC_LIST, k=random.randint(1, 3))
            fam_hist = random.sample(FAMILY_HIST_LIST, k=random.randint(1, 2))
        else:
            if random.random() < 0.35:
                diag_chronic = random.sample(CHRONIC_LIST, k=random.randint(1, 2))
            else:
                diag_chronic = ["No chronic disease diagnosed"]
            
            if random.random() < 0.40:
                fam_hist = random.sample(FAMILY_HIST_LIST, k=random.randint(1, 2))
            else:
                fam_hist = ["No family history"]

        exercise = random.choice(EXERCISE_FREQ)
        activity = random.choice(DAILY_ACTIVITY)
        sugary = random.choice(SUGARY_FREQ)
        smoking = random.choice(SMOKING_STATUS)
        alcohol = random.choice(ALCOHOL_STATUS)
        sleep = random.choice(SLEEP_HOURS)
        diet = random.choice(DIET_TYPES)
        fruits_veg = random.choice(FRUITS_VEG_FREQ)
        fast_food = random.choice(FAST_FOOD_FREQ)
        routine_check = random.choice(ROUTINE_CHECKUP)
        blood_sugar_test = random.choice(BLOOD_SUGAR_TEST)
        health_acc = random.choice(HEALTHCARE_ACCESS)
        med_acc = random.choice(MEDICINES_ACCESS)

        if "Yes" in q9_diab:
            impact = random.choice(DAILY_IMPACT[:3])
            expend = random.choice(EXPENDITURE[1:])
            challenges = random.sample(CHALLENGES, k=random.randint(1, 3))
        else:
            impact = "Not applicable (not diagnosed)"
            expend = "₹0 (No cost / Government supply)"
            challenges = ["No major challenges"]

        awareness_prog = random.choice(AWARENESS_PROGRAMS)
        comm_know = random.choice(COMMUNITY_KNOWLEDGE)
        prev_sugg = random.choice(PREVENTION_IDEAS) if random.random() > 0.3 else ""
        health_sugg = random.choice(HEALTHCARE_IDEAS) if random.random() > 0.3 else ""
        future_part = random.choice(FUTURE_PARTICIPATION)

        ref_id = f"CSP-DEMO-{1000 + i}"

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
            ref_id, loc_type, survey_loc, surveyor,
            "", age_group, gender, occupation, education,
            heard_diab, json.dumps(aware_diseases), learned_source,
            q9_diab, json.dumps(diag_chronic), json.dumps(fam_hist),
            exercise, activity, sugary,
            smoking, alcohol, sleep,
            diet, fruits_veg, fast_food,
            routine_check, blood_sugar_test,
            health_acc, med_acc,
            impact, expend, json.dumps(challenges),
            awareness_prog, comm_know,
            prev_sugg, health_sugg, future_part,
            1, 1, hash_ip(f"synthetic-{i}")
        )

        cursor.execute(format_sql(sql), params)

    conn.commit()
    conn.close()
    return count

if __name__ == '__main__':
    from database import init_db
    init_db()
    count = generate_synthetic_surveys(50)
    print(f"Generated {count} synthetic survey records successfully.")

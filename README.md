# Diabetes & Chronic Disease Community Survey Portal
### Community Survey Project (CSP) 2024

A production-ready, responsive full-stack web application designed for academic research and community health assessment under the **Community Survey Project (CSP)**. The portal collects survey responses regarding Diabetes Mellitus and comorbid chronic diseases across rural, urban, and semi-urban communities, performs descriptive statistical analysis, displays interactive epidemiological visualizations, and exports anonymized datasets for academic research.

---

## 🌟 Key Features

1. **Healthcare-Themed Home Page:**
   - Professional teal (`#0F766E`) and dark blue (`#0F172A`) palette.
   - Real-time live statistics card displaying current sample size ($N$), reported diabetes prevalence, rural vs urban split, and physical inactivity.
   - Explains academic research objectives, survey methodology, and community health pillars.

2. **Standardized 32-Question Survey Module:**
   - Reproduces all 32 questions verbatim from the authoritative questionnaire (`CSP_Diabetes_Survey_Questionnaire.docx`).
   - Grouped into 9 logical sections:
     - **Section 1:** Basic Information (Q1–Q5 + Location Type)
     - **Section 2:** Awareness of Diabetes and Chronic Diseases (Q6–Q8)
     - **Section 3:** Health Status & Family History (Q9–Q11)
     - **Section 4:** Lifestyle and Habits (Q12–Q17)
     - **Section 5:** Diet and Nutrition (Q18–Q20)
     - **Section 6:** Medical Checkups and Treatment (Q21–Q24)
     - **Section 7:** Impact on Daily Life & Expenditures (Q25–Q27)
     - **Section 8:** Community Awareness (Q28–Q29)
     - **Section 9:** Suggestions & Future Participation (Q30–Q32)
     - **Declaration & Informed Consent:** Explicit verification step prior to submission.
   - Preserves original mandatory markers (`*`). Optional questions remain optional.
   - Mobile-first responsive touch cards for single-select (radios), multi-select (checkboxes), and textareas.
   - Interactive animated progress bar and sticky section indicator.
   - **Review Answers Before Submitting:** Modal summary permitting respondents to review all answers before final persistence.

3. **Dual Database Architecture (SQLite & PostgreSQL):**
   - **Local Development:** SQLite by default (`diabetes_survey.db`) with zero configuration.
   - **Cloud Production:** Automatically detects and connects to PostgreSQL when `DATABASE_URL` is set.
   - Safe parameterized queries (`?` for SQLite, `%s` for PostgreSQL) eliminating SQL injection risks.
   - Automated schema and index initialization on boot for both engines.
   - Duplicate submission prevention via rate-limiting IP salt hashing.

4. **Interactive Research Analytics Dashboard:**
   - Protected by session authentication and constant-time credential comparison.
   - KPI metric cards with mathematically defined denominators ($N$).
   - 8 interactive Chart.js visualizations:
     1. Q9 Reported Diabetes Diagnosis Breakdown (Doughnut)
     2. Q10 Chronic Diseases Comorbidities Frequency (Horizontal Bar)
     3. Q2 Age Demographic Representation (Bar)
     4. Community Geographic Classification: Rural vs Urban vs Semi-Urban (Doughnut)
     5. Q12 Physical Activity / Exercise Frequency (Bar)
     6. Age-Specific Reported Diabetes Prevalence Cross-Tabulation (Grouped Bar)
     7. Q22 Blood Glucose Screening Intervals (Bar)
     8. Q23 Distance to Nearest Healthcare Facility / PHC (Bar)
   - Academic descriptive findings panel.
   - Methodological disclaimer regarding cross-sectional observational design vs causal inference.

5. **Anonymized Data Explorer & CSV Export:**
   - Filterable data table by location (Rural / Urban) and Diabetes diagnosis status.
   - Single-response inspection modal with masked respondent identity (`A***` or `Anonymous`).
   - One-click Anonymized CSV export containing all 32 questions formatted for research tools (SPSS, R, Python pandas, Stata) with zero personal identifying leaks.

6. **Production Health & Security Hardening:**
   - Dedicated `/health` endpoint verifying live database connectivity.
   - Strict fail-safe secrets enforcement in production (refuses to start without strong `SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD`).
   - Cookie security: `HttpOnly`, `SameSite=Lax`, and `Secure` (over HTTPS).
   - Flask debug mode disabled in production.
   - Synthetic demo seeding gated and disabled in production to protect real survey data.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.10+ / Flask 3.1+
- **WSGI Server:** Gunicorn 21.2+ (for Linux/Render production)
- **Database:** PostgreSQL (Production via `DATABASE_URL`) / SQLite 3 (Development default)
- **Database Drivers:** `psycopg2-binary>=2.9.9`, built-in `sqlite3`
- **Frontend:** HTML5, CSS3 (Custom Responsive Grid & Variables), Vanilla ES6 JavaScript
- **Visualizations:** Chart.js 4.4+
- **Security:** Timing-attack resistant authentication (`hmac.compare_digest`), parameterized SQL, salted IP hashing, input sanitization

---

## 📁 Directory Structure

```
diabetes_survey_portal/
│
├── app.py                      # Flask routes, validation, admin authentication, CSV streamer, /health probe
├── config.py                   # Production-hardened config, secret validation, secure cookies
├── database.py                 # Dual SQLite / PostgreSQL engine, parameterized queries, health check
├── seed_data.py                # Realistic synthetic demo dataset generator (development only)
├── test_app.py                 # Comprehensive unit & integration test suite (11 tests)
├── requirements.txt            # Python dependencies (Flask, Gunicorn, psycopg2-binary, Werkzeug)
├── Procfile                    # Web process command for Render / cloud PaaS
├── .gitignore                  # Excludes .env, databases, CSV exports, and cache files
├── README.md                   # Setup guide, production environment variables, and deployment steps
│
├── static/
│   ├── css/
│   │   ├── style.css           # Global healthcare theme, header, footer, alert banners
│   │   ├── survey.css          # Multi-step survey wizard, cards, review modal, progress bar
│   │   └── dashboard.css       # Analytics cards, Chart.js wrappers, data tables
│   └── js/
│       ├── survey.js           # Survey wizard, client validation, review modal controller
│       └── dashboard.js        # Chart.js graphs, table search/filter, response inspector
│
└── templates/
    ├── base.html               # Shared layout, navbar, healthcare footer, disclaimers
    ├── index.html              # Home landing page with live quick metrics & CSP mission
    ├── survey.html             # Authoritative 32-question survey wizard + consent step
    ├── survey_success.html     # Confirmation page with audit reference ID & health tips
    ├── login.html              # Admin authentication login page (no exposed credentials)
    ├── dashboard.html          # Protected Research & Analytics Dashboard
    └── about.html              # Academic methodology, ethics, & coordinator guide
```

---

## 🔐 Environment Variables Reference

Configure these environment variables in your deployment platform (e.g., Render Dashboard):

| Variable Name | Environment | Required | Description |
|---|---|---|---|
| `FLASK_ENV` | Production | **Yes** | Set to `production`. Disables debug mode and activates strict security validations. |
| `SECRET_KEY` | Production | **Yes** | High-entropy 64-character random string for session cookie signing. |
| `DATABASE_URL` | Production | **Yes** | PostgreSQL connection URI provided by Render (e.g. `postgresql://user:pass@host/dbname`). |
| `ADMIN_USERNAME` | Production | **Yes** | Secure username for administrative portal access. |
| `ADMIN_PASSWORD` | Production | **Yes** | Strong, unique password for administrative portal access (minimum 8 characters). |
| `ENABLE_DEMO_DATA` | Production | Optional | Defaults to `false` in production. Protects against mock data generation. |
| `PORT` | Production | Managed | Automatically injected by Render (defaults to `5000` locally). |
| `HOST` | Production | Managed | Binds to `0.0.0.0` in production. |

---

## 🚀 Local Development Setup (Windows)

```powershell
# 1. Navigate to project directory
cd C:\Users\SriPr\.gemini\antigravity\scratch\diabetes_survey_portal

# 2. Run the automated test suite
python test_app.py

# 3. Start local development server
python app.py
```
Open your browser at `http://127.0.0.1:5000`.

---

## ☁️ Production Deployment Instructions (GitHub & Render)

### Step 1: Push Project to a Private GitHub Repository
1. Initialize git in the project root:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Production-ready Diabetes Survey Portal"
   ```
2. Create a **Private Repository** on GitHub (e.g., `diabetes-survey-portal`).
3. Push code to GitHub:
   ```bash
   git remote add origin https://github.com/<your-username>/diabetes-survey-portal.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Create a PostgreSQL Database on Render
1. Log in to [render.com](https://render.com).
2. Click **New +** → **PostgreSQL**.
3. Fill in details:
   - **Name:** `csp-diabetes-db`
   - **Database:** `csp_survey_db`
   - **User:** `csp_admin`
   - **Region:** Choose the region closest to your respondents (e.g., *Singapore*, *Frankfurt*, or *Oregon*).
   - **Plan:** Free tier (or Starter for automated daily backups).
4. Click **Create Database**. Render will provision the database and provide an **Internal Database URL**.

### Step 3: Deploy the Web Service on Render
1. Click **New +** → **Web Service** and link your private GitHub repository.
2. Configure settings:
   - **Runtime:** `Python 3`
   - **Region:** Same region as your PostgreSQL instance.
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
3. Add **Environment Variables** in the Render Web Service settings:
   - `FLASK_ENV` = `production`
   - `SECRET_KEY` = *(Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)*
   - `ADMIN_USERNAME` = *(Your chosen secure admin username)*
   - `ADMIN_PASSWORD` = *(Your chosen strong password)*
   - `DATABASE_URL` = *(Paste the Internal Database URL from Step 2)*
   - `ENABLE_DEMO_DATA` = `false`
4. Under **Advanced Settings**:
   - Set **Health Check Path** to `/health`.
5. Click **Create Web Service**.

### Step 4: Health Checks & Verification
- Render will ping `/health`. When the application and PostgreSQL database are operational, it returns `HTTP 200` with `{"status": "healthy", "database": "connected"}`.
- Database tables and indexes are automatically created on first boot via `init_db()`.
- Access the live application URL, complete a test survey submission, log in to the admin dashboard, and verify that the data persists in PostgreSQL.

---

## 📜 Academic Research Disclaimer
This portal is developed strictly for community health research and academic survey data collection. It does not provide medical diagnoses, clinical evaluations, or therapeutic recommendations. All respondents are encouraged to consult qualified healthcare providers for medical advice.

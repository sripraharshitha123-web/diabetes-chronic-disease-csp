import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Environment identification
    ENV = os.environ.get('FLASK_ENV', os.environ.get('ENV', 'development')).lower()
    IS_PRODUCTION = ENV in ('production', 'prod')

    # Security: Secret Key Validation
    _raw_secret_key = os.environ.get('SECRET_KEY')
    _insecure_defaults = {
        'csp-diabetes-survey-secure-secret-key-2024',
        'secret',
        'changeme',
        'admin',
        'default',
        'password'
    }

    if IS_PRODUCTION:
        if not _raw_secret_key or _raw_secret_key.strip() in _insecure_defaults or len(_raw_secret_key.strip()) < 16:
            raise RuntimeError(
                "FATAL CONFIGURATION ERROR: Production deployment requires a secure, high-entropy "
                "SECRET_KEY environment variable (minimum 16 characters). Default or insecure keys are strictly prohibited."
            )
        SECRET_KEY = _raw_secret_key.strip()
    else:
        # Development fallback (only used locally when FLASK_ENV != production)
        SECRET_KEY = _raw_secret_key.strip() if _raw_secret_key else 'dev-csp-survey-local-only-key-not-for-prod'

    # Security: Administrator Credentials Validation
    _raw_admin_user = os.environ.get('ADMIN_USERNAME')
    _raw_admin_pass = os.environ.get('ADMIN_PASSWORD')

    if IS_PRODUCTION:
        if not _raw_admin_user or not _raw_admin_user.strip():
            raise RuntimeError(
                "FATAL CONFIGURATION ERROR: Production deployment requires the ADMIN_USERNAME "
                "environment variable to be set. Default usernames are not permitted."
            )
        if not _raw_admin_pass or _raw_admin_pass.strip() in {'Admin@CSP2024', 'admin', 'password', '123456'} or len(_raw_admin_pass.strip()) < 8:
            raise RuntimeError(
                "FATAL CONFIGURATION ERROR: Production deployment requires the ADMIN_PASSWORD "
                "environment variable to be set to a strong, non-default passphrase (minimum 8 characters)."
            )
        ADMIN_USERNAME = _raw_admin_user.strip()
        ADMIN_PASSWORD = _raw_admin_pass.strip()
    else:
        # Local development defaults
        ADMIN_USERNAME = _raw_admin_user.strip() if _raw_admin_user else 'admin'
        ADMIN_PASSWORD = _raw_admin_pass.strip() if _raw_admin_pass else 'Admin@CSP2024'

    # Database Configuration (PostgreSQL in production, SQLite in development)
    DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'diabetes_survey.db'))
    _raw_db_url = os.environ.get('DATABASE_URL')
    if _raw_db_url:
        # Render and Heroku use 'postgres://', standardize to 'postgresql://' for psycopg2 compatibility
        if _raw_db_url.startswith('postgres://'):
            _raw_db_url = _raw_db_url.replace('postgres://', 'postgresql://', 1)
        DATABASE_URL = _raw_db_url
    else:
        DATABASE_URL = None

    # Production Session Cookies & Header Security
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # Server execution & Debug control
    DEBUG = False if IS_PRODUCTION else (os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1'))
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '0.0.0.0' if IS_PRODUCTION else '127.0.0.1')

    # Feature Flags: Disallow synthetic demo generation in production
    ENABLE_DEMO_DATA = os.environ.get('ENABLE_DEMO_DATA', 'false' if IS_PRODUCTION else 'true').lower() in ('true', '1', 'yes')

    # Project metadata
    PROJECT_NAME = "Community Survey Project (CSP)"
    SURVEY_TITLE = "Diabetes & Chronic Disease Community Survey Portal"

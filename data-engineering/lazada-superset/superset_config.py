"""
Makro Data Service Platform - Apache Superset Configuration
=============================================================
Custom configuration for Superset with Databricks backend,
Redis caching, and user-level row-level security.
"""

import os
from datetime import timedelta
from cachelib.redis import RedisCache

# ─────────────────────────────────────────────
# Core Settings
# ─────────────────────────────────────────────

# Generate a strong random secret key: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "CHANGE_ME_BEFORE_PRODUCTION_USE")

# App name shown in browser tab / header
APP_NAME = "Lazada Data Service Platform"

# Favicon / logo (place files in /app/superset/static/assets/)
APP_ICON = "/static/assets/images/makro_logo.png"
FAVICONS = [{"href": "/static/assets/images/makro_favicon.ico"}]

# Branding colour (hex)
# Makro red: #EF4444
THEME_OVERRIDES = {
    "colors": {
        "primary": {
            "base": "#EF4444",
            "dark1": "#DC2626",
            "dark2": "#B91C1C",
            "light1": "#FCA5A5",
            "light2": "#FEE2E2",
            "light3": "#FFF1F2",
            "light4": "#FFF5F5",
            "light5": "#FFFAFA",
        }
    }
}

# ─────────────────────────────────────────────
# Database (Superset metadata — NOT Databricks)
# ─────────────────────────────────────────────

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://superset:superset@db:5432/superset",
)

# ─────────────────────────────────────────────
# Redis Cache
# ─────────────────────────────────────────────

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_CELERY_DB = 0
REDIS_RESULTS_DB = 1
REDIS_CACHE_DB = 2

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 3600,           # 1 hour
    "CACHE_KEY_PREFIX": "makro_superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": REDIS_CACHE_DB,
}

DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 3600,
    "CACHE_KEY_PREFIX": "makro_data_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": REDIS_CACHE_DB,
}

EXPLORE_FORM_DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_KEY_PREFIX": "makro_explore_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": REDIS_CACHE_DB,
}

# ─────────────────────────────────────────────
# Celery (async queries)
# ─────────────────────────────────────────────

class CeleryConfig:
    broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}"
    worker_prefetch_multiplier = 1
    task_acks_late = False
    task_annotations = {
        "sql_lab.get_sql_results": {"rate_limit": "100/s"},
    }


CELERY_CONFIG = CeleryConfig

# ─────────────────────────────────────────────
# OAuth / Authentication
# ─────────────────────────────────────────────
# Uncomment and configure for Databricks OAuth U2M (user-to-machine)
# This ensures each user authenticates with their own Databricks identity
# and row-level permissions are enforced at the Databricks layer.

# from flask_appbuilder.security.manager import AUTH_OAUTH
# AUTH_TYPE = AUTH_OAUTH

# OAUTH_PROVIDERS = [
#     {
#         "name": "databricks",
#         "icon": "fa-database",
#         "token_key": "access_token",
#         "remote_app": {
#             "client_id": os.environ.get("DATABRICKS_CLIENT_ID"),
#             "client_secret": os.environ.get("DATABRICKS_CLIENT_SECRET"),
#             "server_metadata_url": (
#                 f"https://{os.environ.get('DATABRICKS_HOST')}/.well-known/oauth-authorization-server"
#             ),
#             "api_base_url": f"https://{os.environ.get('DATABRICKS_HOST')}/api/2.0/",
#             "client_kwargs": {"scope": "sql offline_access"},
#         },
#     }
# ]

# AUTH_USER_REGISTRATION = True
# AUTH_USER_REGISTRATION_ROLE = "Gamma"

# ─────────────────────────────────────────────
# Row Level Security
# ─────────────────────────────────────────────
# RLS is enforced via Superset's built-in RLS feature.
# Each Superset user/role maps to a class_name filter clause,
# exactly mirroring the user_categories logic from the Streamlit app.
#
# Example RLS filter for a Dry Food buyer:
#   Table: niq_sales_perf
#   Group key: category_dry_food
#   Clause: class_name IN ('DRY FOOD')
#
# Configure via Superset UI: Security → Row Level Security

ENABLE_ROW_LEVEL_SECURITY = True

# ─────────────────────────────────────────────
# Feature Flags
# ─────────────────────────────────────────────

FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,     # Jinja templating in SQL
    "DASHBOARD_RBAC": True,                 # Dashboard-level role permissions
    "EMBEDDABLE_CHARTS": True,
    "DRILL_TO_DETAIL": True,
    "DRILL_BY": True,
    "DATAPANEL_CLOSED_BY_DEFAULT": False,
    "ALERT_REPORTS": True,
    "THUMBNAILS": True,
    "LISTVIEWS_DEFAULT_CARD_VIEW": False,
    "DASHBOARD_FILTERS_EXPERIMENTAL": True,
    "ENABLE_JAVASCRIPT_CONTROLS": False,    # Keep False for security
    "KV_STORE": True,
    "GLOBAL_ASYNC_QUERIES": True,
    "VERSIONED_EXPORT": True,
}

# ─────────────────────────────────────────────
# SQL Lab
# ─────────────────────────────────────────────

SQLLAB_TIMEOUT = 300                        # 5 minutes
SUPERSET_WEBSERVER_TIMEOUT = 300
SQL_MAX_ROW = 100000
DISPLAY_MAX_ROW = 10000

# Allow Jinja templating in SQL Lab (for {{ current_user() }}, etc.)
ENABLE_TEMPLATE_PROCESSING = True

# ─────────────────────────────────────────────
# Talisman / Security Headers
# ─────────────────────────────────────────────

TALISMAN_ENABLED = True
TALISMAN_CONFIG = {
    "content_security_policy": {
        "default-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        "img-src": ["'self'", "data:", "blob:"],
        "worker-src": ["blob:"],
        "connect-src": ["'self'"],
    },
    "force_https": False,                   # Set True behind HTTPS proxy
}

# ─────────────────────────────────────────────
# Email (for Alerts & Reports)
# ─────────────────────────────────────────────

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_STARTTLS = True
SMTP_SSL = False
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_MAIL_FROM = os.environ.get("SMTP_MAIL_FROM", "makro-data@cpaxtra.co.th")
EMAIL_REPORTS_SUBJECT_PREFIX = "[Makro Data] "

# ─────────────────────────────────────────────
# Webserver
# ─────────────────────────────────────────────

SUPERSET_WEBSERVER_ADDRESS = "0.0.0.0"
SUPERSET_WEBSERVER_PORT = 8088
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = ["superset.views.core.log"]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False               # Set True when behind HTTPS

# ─────────────────────────────────────────────
# Miscellaneous
# ─────────────────────────────────────────────

ROW_LIMIT = 50000
VIZ_ROW_LIMIT = 50000
SAMPLES_ROW_LIMIT = 1000
DEFAULT_SQLLAB_LIMIT = 1000

# Supported Databricks time grains
TIME_GRAIN_ADDON_EXPRESSIONS = {}

# Logging
ENABLE_TIME_ROTATE = True
TIME_ROTATE_LOG_LEVEL = "INFO"
FILENAME = os.path.join("/app/superset_home", "superset.log")

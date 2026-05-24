"""
Sistema de Agendamento Clínico Seguro
Configurações Django - Segurança by Design
Samuel Oliveira Acácio - RGM: 11231100856
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── SEGURANÇA BÁSICA ─────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-troque-em-producao-obrigatoriamente')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ─── APPS ─────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 2FA
    'django_otp',
    'django_otp.plugins.otp_totp',
    # Proteção brute force (RNF02)
    'axes',
    # Apps do projeto
    'apps.autenticacao',
    'apps.recuperacao',
    'apps.auditoria',
    'apps.lgpd',
    'apps.agendamento',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',          # 2FA (RNE02)
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',               # Rate limit (RNF02)
    'apps.autenticacao.middleware.SessionTimeoutMiddleware',  # Sessão (RNF03)
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ─── BANCO DE DADOS - PostgreSQL (RNF, req 3.4) ───────────────────────────────
DATABASES = {
    'default':  {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'clinica_segura',
        'USER': 'postgres',
        'PASSWORD': 'Clinica2026',
        'HOST': 'localhost',
        'PORT': '5433',
    }
    }


# ─── HASH DE SENHA - PBKDF2 com SHA256 (RNF01, req 1.1) ─────────────────────
# Django usa PBKDF2+SHA256 por padrão com salt único por usuário
# Parâmetros justificados: 870.000 iterações (OWASP 2024)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # PBKDF2+SHA256
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Fallback Argon2
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── SESSÃO SEGURA (RNF03, req 1.9 / 1.10) ───────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 900              # 15 minutos (RNF03)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = not DEBUG     # HTTPS only em produção
SESSION_COOKIE_HTTPONLY = True        # Impede acesso via JS
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True     # Renova o timeout a cada request

# ─── CSRF / COOKIES ───────────────────────────────────────────────────────────
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True

# ─── HTTPS / TLS (RNF04, req 3.1 / 3.2) ──────────────────────────────────────
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ─── PROTEÇÃO BRUTE FORCE - django-axes (RNF02, req 1.11) ────────────────────
AXES_FAILURE_LIMIT = 5                 # Bloqueia após 5 tentativas
AXES_COOLOFF_TIME = 1                  # 1 hora de bloqueio
AXES_LOCKOUT_CALLABLE = 'apps.autenticacao.utils.axes_lockout_handler'
AXES_RESET_ON_SUCCESS = True
AXES_ENABLE_ACCESS_FAILURE_LOG = True
AXES_BACKEND_ORDER = ['axes.backends.AxesStandaloneBackend']

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ─── 2FA (RNE02, req 1.5 / 1.6) ──────────────────────────────────────────────
OTP_TOTP_ISSUER = 'Clínica Segura'

# ─── LOGS DE AUDITORIA (RNF05, req 5.1 a 5.4) ────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'auditoria': {
            'format': '[{asctime}] [{levelname}] [{name}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%dT%H:%M:%S',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'auditoria',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'auditoria',
        },
    },
    'loggers': {
        'auditoria': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'axes': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# ─── ESTÁTICOS E INTERNACIONALIZAÇÃO ─────────────────────────────────────────
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'auth.User'

LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/painel/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# ─── EMAIL (recuperação de senha, req 2.x) ────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Troque em prod
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'noreply@clinicasegura.com.br'

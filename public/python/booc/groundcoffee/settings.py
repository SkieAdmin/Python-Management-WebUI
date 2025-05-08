from pathlib import Path
import os

# ──────────────────────────────────────────────────────────────────────────────
# BASE DIR
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────────────────────────────────────────────
# SECURITY
# ──────────────────────────────────────────────────────────────────────────────
SECRET_KEY = 'your-secret-key'
DEBUG = True
ALLOWED_HOSTS = []


# ──────────────────────────────────────────────────────────────────────────────
# APPLICATIONS
# ──────────────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your apps
    'shop',               # storefront
    'shop.adminpanel',    # custom admin panel
]


# ──────────────────────────────────────────────────────────────────────────────
# MIDDLEWARE
# ──────────────────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ──────────────────────────────────────────────────────────────────────────────
# URL CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
ROOT_URLCONF = 'groundcoffee.urls'


# ──────────────────────────────────────────────────────────────────────────────
# TEMPLATES
# ──────────────────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # ← This must include your project-level templates folder:
        'DIRS': [ BASE_DIR / 'templates' ],
        'APP_DIRS': True,   # ← must be True so Django will also look in app/templates/
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


# ──────────────────────────────────────────────────────────────────────────────
# WSGI
# ──────────────────────────────────────────────────────────────────────────────
WSGI_APPLICATION = 'groundcoffee.wsgi.application'


# ──────────────────────────────────────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME':   BASE_DIR / 'db.sqlite3',
    }
}


# ──────────────────────────────────────────────────────────────────────────────
# AUTH PASSWORD VALIDATORS
# ──────────────────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# INTERNATIONALIZATION
# ──────────────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Manila'    # set to user's local timezone
USE_I18N      = True
USE_L10N      = True
USE_TZ        = True


# ──────────────────────────────────────────────────────────────────────────────
# STATIC FILES (CSS, JS, etc.)
# ──────────────────────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'shop' / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ──────────────────────────────────────────────────────────────────────────────
# MEDIA FILES (User uploads)
# ──────────────────────────────────────────────────────────────────────────────
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ──────────────────────────────────────────────────────────────────────────────
# DEFAULT PRIMARY KEY FIELD TYPE
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ──────────────────────────────────────────────────────────────────────────────
# CUSTOM ADMIN AUTH REDIRECTS
# ──────────────────────────────────────────────────────────────────────────────
# When @login_required or @user_passes_test() redirects:
LOGIN_URL           = 'shop_admin:login'       # e.g. /adminpanel/login/
LOGIN_REDIRECT_URL  = 'shop_admin:dashboard'   # after successful login
LOGOUT_REDIRECT_URL = 'shop_admin:login'       # after logout


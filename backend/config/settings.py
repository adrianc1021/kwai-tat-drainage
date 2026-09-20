from pathlib import Path
import os, secrets
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
SITE_DIR = PROJECT_DIR / 'production' / 'site'
PRIVATE_DIR = Path(os.environ.get('CMS_DATA_DIR', BASE_DIR / 'private'))
PRIVATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
secret_file = PRIVATE_DIR / 'secret.key'
if not secret_file.exists():
    fd = os.open(secret_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f: f.write(secrets.token_urlsafe(64))
SECRET_KEY = secret_file.read_text().strip()
PRODUCTION = os.environ.get('CMS_PRODUCTION') == '1'
DEBUG = False
ALLOWED_HOSTS = os.environ.get('CMS_ALLOWED_HOSTS','127.0.0.1,localhost,testserver').split(',')
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','cms.apps.CmsConfig']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware','cms.middleware.Headers']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION='config.wsgi.application'
DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':PRIVATE_DIR/'cms.sqlite3','OPTIONS':{'timeout':20}}}
AUTH_PASSWORD_VALIDATORS=[{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator','OPTIONS':{'min_length':12}},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE='zh-hant'
TIME_ZONE='Asia/Hong_Kong'
USE_TZ=True
STATIC_URL='/assets/'
STATIC_ROOT=BASE_DIR/'staticfiles'
STATICFILES_DIRS=[BASE_DIR/'static']
MEDIA_ROOT=PRIVATE_DIR/'media'
MEDIA_URL='/media/'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
LOGIN_URL='/manage/login/'
LOGIN_REDIRECT_URL='/manage/'
LOGOUT_REDIRECT_URL='/manage/login/'
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE='Strict'
SESSION_COOKIE_AGE=3600
SESSION_SAVE_EVERY_REQUEST=False
CSRF_COOKIE_SAMESITE='Strict'
SESSION_COOKIE_SECURE=PRODUCTION
CSRF_COOKIE_SECURE=PRODUCTION
SECURE_SSL_REDIRECT=PRODUCTION
SECURE_HSTS_SECONDS=31536000 if PRODUCTION else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS=PRODUCTION
SECURE_HSTS_PRELOAD=PRODUCTION
SECURE_REFERRER_POLICY='same-origin'
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS='DENY'
DATA_UPLOAD_MAX_MEMORY_SIZE=12*1024*1024
FILE_UPLOAD_MAX_MEMORY_SIZE=12*1024*1024
FILE_UPLOAD_PERMISSIONS=0o600
# No URL/query/IP access log persistence; analytics uses an allowlist instead.
LOGGING={'version':1,'disable_existing_loggers':False,'handlers':{'null':{'class':'logging.NullHandler'}},'loggers':{'django.server':{'handlers':['null'],'propagate':False}}}

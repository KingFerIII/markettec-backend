"""
Django settings for markettec project.
"""

from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv # Para .env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Cargar variables de .env ---
load_dotenv(BASE_DIR / '.env')
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't']
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1, 172.200.235.24').split(',')
# ---------------------------------


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps de Terceros
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'django_rest_passwordreset',
    'corsheaders',
    'drf_spectacular', # Para OpenAPI/Swagger

    # Mis Apps
    'apps.users.apps.UsersConfig', # Configuración de Signals
    'apps.products',
    'apps.orders',
    'apps.audits',
    'apps.reports',
    'apps.reviews',
    'apps.favorites',
    'apps.chat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # ¡Importante!
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'markettec.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'markettec.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True


# --- Archivos Estáticos (para /admin/) y Archivos de Medios (imágenes) ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static' # Para 'collectstatic' en producción

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' # Para 'product_image' y 'profile_image'
# -----------------------------------------------------------------


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Configuración de DRF (API) ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication', # Para el login del navegador
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer', # Para la API "fea"
    ),
    # Configuración de OpenAPI/Swagger
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # --- ¡AGREGA ESTO PARA LA PAGINACIÓN! ---
    #'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    #'PAGE_SIZE': 20, # Manda de 20 en 20 items (puedes cambiar el número)

    
}

# --- Configuración de JWT (Login) ---
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),

    # --- ¡ESTA ES LA LÍNEA NUEVA! ---
    # Le dice a simple_jwt que use nuestro serializer personalizado
    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.serializers.MyTokenObtainPairSerializer',
}

# --- Configuración de OpenAPI/Swagger ---
SPECTACULAR_SETTINGS = {
    'TITLE': 'MarketTec API',
    'DESCRIPTION': 'Documentación de la API para el proyecto MarketTec (App Android y Panel Admin)',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # ¡ESTO ARREGLA EL BUG #4! (Le dice a Swagger dónde está el Login)
    'SWAGGER_UI_SETTINGS': {
        "deepLinking": True,
        "persistAuthorization": True,
    },
    'AUTHENTICATION_WHITELIST': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
    
    # ----------------------------------------------------
    #  ¡AQUÍ SE AGREGA LA LISTA DE TAGS PARA EL ORDEN!
    # ----------------------------------------------------
    'TAGS': [
        {'name': '1. Autenticación', 'description': 'Registro, inicio y restablecimiento de sesión.'},
        {'name': '2. Usuarios', 'description': 'Gestión de perfiles y acciones de administración (banear).'},
        {'name': '3. Productos y Categorías', 'description': 'Gestión de productos y sus categorías.'},
        {'name': '4. Reseñas', 'description': 'Gestión de reseñas de productos.'},
        {'name': '5. Favoritos', 'description': 'Gestión de productos favoritos.'},
        {'name': '6. Pedidos', 'description': 'Gestión del ciclo de vida de los pedidos.'},
        {'name': '7. Reportes', 'description': 'Creación y gestión de reportes de usuarios.'},
        {'name': '8. Auditoría (Admin)', 'description': 'Consulta del historial de acciones (solo Admin).'},
        {'name': '9. Chat', 'description': 'Mensajería entre cliente y vendedor (Texto, Fotos, Audio y Ubicación).'},
    ],
}

# --- Configuración de Email (para Reseteo de Contraseña) ---
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# --- Configuración de CORS (para React) ---
CORS_ALLOWED_ORIGINS = [
    "http://172.200.235.24:8000",
    "http://172.200.235.24",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CSRF_TRUSTED_ORIGINS = [
    "http://172.200.235.24",
    "http://172.200.235.24:8000",
]
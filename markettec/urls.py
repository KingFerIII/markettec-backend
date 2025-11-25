# En: markettec/urls.py

from django.contrib import admin
from django.urls import path, include

# --- Importaciones para MEDIA! ---
from django.conf import settings
from django.conf.urls.static import static

# --- ¡Importaciones para SWAGGER! ---
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# --- ¡Importaciones para el LOGIN! ---
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from apps.users.serializers import MyTokenObtainPairSerializer 
from drf_spectacular.utils import extend_schema

# --- ¡Clases Decoradas (CORREGIDAS)! ---
# Aquí creamos unas "mini-clases" para decorar solo el método POST y no causar el crash
class DecoratedTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    
    @extend_schema(
        tags=['1. Autenticación'],
        summary="1. Iniciar Sesión (Obtener Token)",
        description="Envía 'username' y 'password' para recibir un 'access_token' y 'refresh_token'.",
        responses={200: TokenObtainPairView.serializer_class}, # <-- ¡COMA AÑADIDA!
        # --- ¡AÑADIDO PARA ORDEN 1! ---
        operation_id='1_token_obtain_pair'
        # -----------------------------
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class DecoratedTokenRefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer # <--- Reafirmamos esta corrección
    
    @extend_schema(
        tags=['1. Autenticación'],
        summary="2. Refrescar Token",
        description="Envía un 'refresh_token' válido para recibir un 'access_token' nuevo.",
        responses={200: TokenRefreshView.serializer_class}, # <-- ¡COMA AÑADIDA!
        # --- ¡AÑADIDO PARA ORDEN 2! ---
        operation_id='2_token_refresh'
        # -----------------------------
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

# --- FIN DE NUEVAS CLASES ---


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- Rutas de Login (ACTUALIZADAS) ---
    path('api/token/', DecoratedTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', DecoratedTokenRefreshView.as_view(), name='token_refresh'),

    # --- Rutas de tus Apps ---
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.products.urls')),
    path('api/', include('apps.orders.urls')),
    path('api/', include('apps.audits.urls')),
    path('api/', include('apps.reports.urls')),
    path('api/', include('apps.reviews.urls')),
    path('api/', include('apps.favorites.urls')), 
    path('api-auth/', include('rest_framework.urls')),
    path('api/password_reset/', include('apps.users.password_reset_urls')),
    path('api/', include('apps.chat.urls')),


    # --- Rutas de SWAGGER (OpenAPI) ---
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# --- Servir archivos de MEDIA (imágenes) en DESARROLLO ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
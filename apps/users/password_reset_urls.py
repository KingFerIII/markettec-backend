# En: apps/users/password_reset_urls.py

from django.urls import path
from .views_spectacular import (
    SpectacularResetPasswordRequestToken,
    SpectacularResetPasswordConfirm,
    SpectacularResetPasswordValidateToken
)

app_name = 'password_reset'

urlpatterns = [
    # Mapea las rutas a tus vistas decoradas (que ya tienen el extend_schema)
    path('', SpectacularResetPasswordRequestToken.as_view(), name='reset-password-request'),
    path('confirm/', SpectacularResetPasswordConfirm.as_view(), name='reset-password-confirm'),
    path('validate_token/', SpectacularResetPasswordValidateToken.as_view(), name='reset-password-validate'),
]
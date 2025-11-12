# En: apps/users/views_spectacular.py

from drf_spectacular.utils import extend_schema
from django_rest_passwordreset.views import ResetPasswordRequestToken
from django_rest_passwordreset.views import ResetPasswordConfirm
from django_rest_passwordreset.views import ResetPasswordValidateToken
from rest_framework import serializers

# --- Serializadores para documentar el Request Body (Cuerpo de Solicitud) ---

class PasswordResetRequestSerializer(serializers.Serializer):
    """ Para POST /password_reset/ """
    email = serializers.EmailField(
        required=True, 
        help_text="Correo electrónico para enviar el token de restablecimiento."
    )

class PasswordResetTokenValidateSerializer(serializers.Serializer):
    """ Para POST /password_reset/validate_token/ """
    token = serializers.CharField(
        required=True, 
        help_text="Token recibido por email."
    )

class PasswordResetTokenConfirmSerializer(serializers.Serializer):
    """ Para POST /password_reset/confirm/ """
    token = serializers.CharField(required=True, help_text="Token recibido por email.")
    password = serializers.CharField(required=True, help_text="Nueva contraseña.")
    password_confirm = serializers.CharField(required=True, help_text="Confirmación de la nueva contraseña.")


# --- Vistas Decoradas (Control del Orden con el Summary) ---

@extend_schema(
    tags=['1. Autenticación'],
    summary="3. Solicitud de Restablecimiento de Contraseña", 
    description="Envía el email para iniciar el proceso.",
    request=PasswordResetRequestSerializer,
    operation_id='3_reset_request', # <--- ¡AÑADIDO PARA FORZAR ORDEN!
    responses={200: {'description': 'Token enviado al email.'}}
)
class SpectacularResetPasswordRequestToken(ResetPasswordRequestToken):
    pass


@extend_schema(
    tags=['1. Autenticación'],
    summary="4. Validar Token de Contraseña", 
    description="Verifica si el token de restablecimiento recibido es válido.",
    request=PasswordResetTokenValidateSerializer,
    operation_id='4_reset_validate', # <--- ¡AÑADIDO PARA FORZAR ORDEN!
    responses={200: {'description': 'Token válido.'}, 400: {'description': 'Token inválido/expirado.'}}
)
class SpectacularResetPasswordValidateToken(ResetPasswordValidateToken):
    pass


@extend_schema(
    tags=['1. Autenticación'],
    summary="5. Confirmar Restablecimiento de Contraseña", 
    description="Envía el token y las nuevas contraseñas.",
    request=PasswordResetTokenConfirmSerializer,
    operation_id='5_reset_confirm', # <--- ¡AÑADIDO PARA FORZAR ORDEN!
    responses={200: {'description': 'Contraseña actualizada exitosamente.'}}
)
class SpectacularResetPasswordConfirm(ResetPasswordConfirm):
    pass
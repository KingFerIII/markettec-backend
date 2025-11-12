# En: apps/users/serializers.py
# (¡Versión completa y corregida para la lógica de Baneo!)

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from .models import Profile  
from apps.audits.models import AuditLog

# --- ¡NUEVAS IMPORTACIONES PARA EL LOGIN SEGURO! ---
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.translation import gettext_lazy as _

User = get_user_model()

# --- 1. SERIALIZER PÚBLICO (Para la API de Productos) ---
# (Este se queda como lo teníamos)
class PublicProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para MOSTRAR PÚBLICAMENTE al vendedor.
    (Solo muestra campos no sensibles)
    """
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    
    class Meta:
        model = Profile
        fields = [
            'first_name', 
            'profile_image',
            'career',
        ]

# --- 2. SERIALIZER PRIVADO (Para el Panel de ADMIN) ---
# (Este SÍ incluye los campos de baneo para que el Admin los vea)
class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para LEER Y ESCRIBIR los datos PRIVADOS del Perfil.
    (Usado por el UserSerializer anidado del Admin)
    """
    class Meta:
        model = Profile
        fields = [
            'role', 
            'phone_number',
            'control_number',
            'career',
            'date_of_birth',
            'profile_image',
            'is_banned',
            'ban_reason'
        ]

# --- 3. SERIALIZER DE USUARIO (Para el Panel de ADMIN) ---
# (Este SÍ incluye el ProfileSerializer completo)
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer principal del Usuario (PARA ADMINS).
    Muestra los datos del User Y anida los datos del Profile completo.
    """
    email = serializers.EmailField(
        required=False,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    
    profile = ProfileSerializer() # <-- Anida el serializer PRIVADO (con baneo)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'profile']

    # --- MÉTODO 'UPDATE' COMPLETO (Para el Admin) ---
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance = super().update(instance, validated_data)
        profile = instance.profile
        
        profile.role = profile_data.get('role', profile.role)
        profile.phone_number = profile_data.get('phone_number', profile.phone_number)
        profile.control_number = profile_data.get('control_number', profile.control_number)
        profile.career = profile_data.get('career', profile.career)
        profile.date_of_birth = profile_data.get('date_of_birth', profile.date_of_birth)
        profile.is_banned = profile_data.get('is_banned', profile.is_banned)
        profile.ban_reason = profile_data.get('ban_reason', profile.ban_reason)

        if 'profile_image' in profile_data:
            profile.profile_image = profile_data.get('profile_image')

        profile.save()
        return instance

# --- ¡NUEVAS CLASES PARA EL PERFIL PÚBLICO DEL USUARIO! ---
# --- (Implementan el Bug #10) ---

class SimpleProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil PÚBLICO del usuario (GET /api/users/profile/)
    Oculta los campos de baneo.
    """
    class Meta:
        model = Profile
        fields = [
            'role', 
            'phone_number',
            'control_number',
            'career',
            'date_of_birth',
            'profile_image'
            # Nota: 'is_banned' y 'ban_reason' están ocultos
        ]

class SimpleUserSerializer(serializers.ModelSerializer):
    """
    Serializer PÚBLICO del Usuario (GET /api/users/profile/)
    Usa el SimpleProfileSerializer.
    """
    profile = SimpleProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'profile']
# --------------------------------------------------------


# --- ¡NUEVA CLASE PARA EL LOGIN SEGURO! ---
# --- (Implementa el Bug #10) ---

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer de Login Personalizado.
    Revisa si el usuario está baneado ANTES de darle un token.
    """
    @classmethod
    def get_token(cls, user):
        # Esta función se llama si el user/pass son correctos
        
        # --- ¡NUESTRA LÓGICA DE BANEO! ---
        if hasattr(user, 'profile') and user.profile.is_banned:
            # Si está baneado, lanzamos un error de "no autorizado"
            raise serializers.ValidationError(
                _("Tu cuenta ha sido baneada. Contacta al administrador."), 
                code='authorization'
            )
        # ----------------------------------
            
        # Si no está baneado, continúa con el login normal
        token = super().get_token(user)
        return token
# ---------------------------------------


# --- 4. SERIALIZER DE REGISTRO (Para /api/register/) ---
# (Este se queda como lo teníamos)
class RegisterSerializer(serializers.ModelSerializer):
    # ... (Campos del User: first_name, username, email, etc.) ...
    first_name = serializers.CharField(required=True, label='Nombre completo')
    username = serializers.CharField(
        required=True, label='Nombre de usuario',
        validators=[UniqueValidator(queryset=User.objects.all(), message="Este nombre de usuario ya existe.")]
    )
    email = serializers.EmailField(
        required=True, label='Correo electrónico',
        validators=[UniqueValidator(queryset=User.objects.all(), message="Este correo electrónico ya existe.")]
    )
    password = serializers.CharField(write_only=True, required=True, label='Contraseña')
    password2 = serializers.CharField(write_only=True, required=True, label='Confirmar contraseña')

    # ... (Campos del Profile: control_number, career, etc.) ...
    control_number = serializers.CharField(required=True, label='Número de Control', write_only=True)
    career = serializers.CharField(required=True, label='Carrera', write_only=True)
    phone_number = serializers.CharField(required=True, label='Número de Teléfono', write_only=True)
    date_of_birth = serializers.DateField(required=True, label='Fecha de Nacimiento', write_only=True)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'username', 'email', 'password', 'password2',
            'control_number', 'career', 'phone_number', 'date_of_birth'
        ]

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return data

    def create(self, validated_data):
        # ... (lógica de create) ...
        profile_data = {
            'control_number': validated_data.pop('control_number'),
            'career': validated_data.pop('career'),
            'phone_number': validated_data.pop('phone_number'),
            'date_of_birth': validated_data.pop('date_of_birth')
        }
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name'),
            'password': validated_data.pop('password')
        }
        validated_data.pop('password2') 
        user = User.objects.create_user(**user_data)
        Profile.objects.filter(user=user).update(**profile_data)

        # ... (lógica de bitácora) ...
        try:
            AuditLog.objects.create(
                user=user,
                action='USER_REGISTERED',
                details=f"Nuevo usuario registrado: '{user.username}' (ID: {user.id})"
            )
        except ImportError:
            pass

        return user
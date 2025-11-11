# En: apps/users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from .models import Profile  
from apps.audits.models import AuditLog # Importamos la bitácora

User = get_user_model()

# --- 1. SERIALIZER PÚBLICO (Para la API de Productos) ---
class PublicProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para MOSTRAR PÚBLICAMENTE al vendedor.
    (Corregido: Sin semester/shift)
    """
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    
    class Meta:
        model = Profile
        fields = [
            'first_name', 
            'profile_image',
            'career',
            # 'semester' y 'shift' eliminados
        ]

# --- 2. SERIALIZER PRIVADO (Para la API de Perfil del Usuario) ---
class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para LEER Y ESCRIBIR los datos PRIVADOS del Perfil.
    (Corregido: Sin semester/shift y sin read_only_fields)
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
            'ban_reason',
            # 'semester' y 'shift' eliminados
            # 'vendor_status' eliminado (modelo marketplace abierto)
        ]
        # ¡IMPORTANTE! Quitamos 'read_only_fields' para que el 'role' sea editable
        # a través del UserSerializer.


# --- 3. SERIALIZER DE USUARIO (Para /api/users/ y /api/users/profile/) ---
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer principal del Usuario.
    Muestra los datos del User Y anida los datos del Profile.
    """
    email = serializers.EmailField(
        required=False,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    
    profile = ProfileSerializer() # <-- Anida el serializer privado

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'profile']

    # --- ¡MÉTODO 'UPDATE' CORREGIDO Y COMPLETO! ---
    def update(self, instance, validated_data):
        """
        Maneja la actualización del User y su Profile anidado.
        (Esta es la lógica que permite al frontend editar todo)
        """
        # 1. Obtenemos los datos del perfil, si es que vienen
        profile_data = validated_data.pop('profile', {})
        
        # 2. Actualizamos los campos del User (ej. email, first_name)
        instance = super().update(instance, validated_data)

        # 3. Actualizamos los campos del Profile
        # Usamos .get() para actualizar solo los campos que se enviaron
        profile = instance.profile
        
        profile.role = profile_data.get('role', profile.role)
        profile.phone_number = profile_data.get('phone_number', profile.phone_number)
        profile.control_number = profile_data.get('control_number', profile.control_number)
        profile.career = profile_data.get('career', profile.career)
        profile.date_of_birth = profile_data.get('date_of_birth', profile.date_of_birth)
        profile.is_banned = profile_data.get('is_banned', profile.is_banned)
        profile.ban_reason = profile_data.get('ban_reason', profile.ban_reason)
        # Maneja la imagen por separado (si se envía)
        if 'profile_image' in profile_data:
            profile.profile_image = profile_data.get('profile_image')

        profile.save()

        return instance


# --- 4. SERIALIZER DE REGISTRO (Para /api/register/) ---
class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para CREAR un nuevo usuario con perfil completo.
    (Corregido: Sin semester/shift)
    """
    
    # --- Campos del User ---
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

    # --- Campos del Profile (con write_only=True) ---
    control_number = serializers.CharField(required=True, label='Número de Control', write_only=True)
    career = serializers.CharField(required=True, label='Carrera', write_only=True)
    phone_number = serializers.CharField(required=True, label='Número de Teléfono', write_only=True)
    date_of_birth = serializers.DateField(required=True, label='Fecha de Nacimiento', write_only=True)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'username', 'email', 'password', 'password2',
            # Campos del perfil
            'control_number', 'career', 'phone_number', 'date_of_birth'
            # 'semester' y 'shift' eliminados
        ]

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return data

    def create(self, validated_data):
        # 1. Sacamos los datos del perfil
        profile_data = {
            'control_number': validated_data.pop('control_number'),
            'career': validated_data.pop('career'),
            'phone_number': validated_data.pop('phone_number'),
            'date_of_birth': validated_data.pop('date_of_birth')
            # 'semester' y 'shift' eliminados
        }
        
        # 2. Sacamos los datos del User
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name'),
            'password': validated_data.pop('password')
        }
        validated_data.pop('password2') 
        
        # 3. Creamos el User
        user = User.objects.create_user(**user_data)
        
        # 4. Actualizamos el Profile
        Profile.objects.filter(user=user).update(**profile_data)

        # 5. Conectamos la bitácora
        try:
            AuditLog.objects.create(
                user=user,
                action='USER_REGISTERED',
                details=f"Nuevo usuario registrado: '{user.username}' (ID: {user.id})"
            )
        except ImportError:
            pass

        return user
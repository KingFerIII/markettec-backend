# En: apps/users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from .models import Profile  
from apps.audits.models import AuditLog
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.translation import gettext_lazy as _

User = get_user_model()

# --- 1. SERIALIZER PÚBLICO (Para la API de Productos/Vendedores) ---
class PublicProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para MOSTRAR PÚBLICAMENTE al vendedor.
    (Solo muestra campos no sensibles)
    """
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    
    class Meta:
        model = Profile
        fields = [
            'id',           # ID del Perfil
            'user_id',      # ID del Usuario (¡Vital para el Chat!)
            'first_name', 
            'username',
            'profile_image',
            'career',
        ]

# --- 2. SERIALIZER PRIVADO (Para el Panel de ADMIN) ---
class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para LEER Y ESCRIBIR los datos PRIVADOS del Perfil.
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

# --- 3. SERIALIZER DE USUARIO (Para el Panel de ADMIN y Edición de Perfil) ---
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer principal del Usuario.
    """
    email = serializers.EmailField(
        required=False,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    
    # Hacemos el perfil opcional para evitar errores de validación si no se envía
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'profile']

    def update(self, instance, validated_data):
        # 1. Intentamos obtener datos anidados (Formato JSON web estandar)
        profile_data = validated_data.pop('profile', {})
        
        # 2. MANIOBRA DE RESCATE (Para Android/Multipart)
        # Si profile_data está vacío (porque Android mandó todo plano),
        # buscamos los campos "sueltos" en los datos crudos (self.initial_data).
        if not profile_data:
            raw_data = self.initial_data
            # Lista de campos que pertenecen al modelo Profile
            profile_fields = ['role', 'phone_number', 'control_number', 'career', 'date_of_birth', 'profile_image']
            
            for field in profile_fields:
                if field in raw_data:
                    # Agregamos el dato al diccionario profile_data
                    profile_data[field] = raw_data[field]

        # 3. Actualizamos User (first_name, email)
        instance = super().update(instance, validated_data)
        
        # 4. Actualizamos Profile
        profile = instance.profile
        
        for attr, value in profile_data.items():
            if value is not None: # Solo actualizamos si enviaron un valor
                setattr(profile, attr, value)
            
        profile.save()
        return instance

# --- SERIALIZERS PARA EL PERFIL PÚBLICO DEL USUARIO ---
class SimpleProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'role', 
            'phone_number',
            'control_number',
            'career',
            'date_of_birth',
            'profile_image'
        ]

class SimpleUserSerializer(serializers.ModelSerializer):
    profile = SimpleProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'profile']

# --- LOGIN SEGURO (Baneo) ---
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        if hasattr(user, 'profile') and user.profile.is_banned:
            raise serializers.ValidationError(
                _("Tu cuenta ha sido baneada. Contacta al administrador."), 
                code='authorization'
            )
        token = super().get_token(user)
        return token

# --- 4. SERIALIZER DE REGISTRO ---
class RegisterSerializer(serializers.ModelSerializer):
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

        try:
            AuditLog.objects.create(
                user=user,
                action='USER_REGISTERED',
                details=f"Nuevo usuario registrado: '{user.username}' (ID: {user.id})"
            )
        except Exception:
            pass

        return user
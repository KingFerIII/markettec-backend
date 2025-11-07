# En: apps/users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from .models import Profile  # <-- IMPORTANTE: Importa el Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para LEER los datos del Perfil.
    (Actualizado para mostrar los campos de registro y quitar 'store_name')
    """
    class Meta:
        model = Profile
        fields = [
            'role', 
            'vendor_status', 
            'phone_number',
            
            # --- Campos nuevos añadidos ---
            'control_number',
            'career',
            'date_of_birth',
            'profile_image',
        ]


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer principal del Usuario.
    Muestra los datos del User Y anida los datos del Profile.
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    
    # --- ¡LA CLAVE! Anidamos el ProfileSerializer ---
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile'] # <-- AÑADIDO 'profile'

    # (Lógica opcional para permitir actualizar el teléfono desde el user endpoint)
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance = super().update(instance, validated_data)
        profile = instance.profile
        profile.phone_number = profile_data.get('phone_number', profile.phone_number)
        profile.store_name = profile_data.get('store_name', profile.store_name)
        profile.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para CREAR un nuevo usuario con perfil completo.
    (Versión corregida con write_only=True)
    """
    
    # --- Campos del User ---
    first_name = serializers.CharField(
        required=True, label='Nombre completo'
    )
    username = serializers.CharField(
        required=True, 
        label='Nombre de usuario',
        validators=[UniqueValidator(queryset=User.objects.all(), message="Este nombre de usuario ya existe.")]
    )
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Este correo electrónico ya existe.")],
        label='Correo electrónico'
    )
    password = serializers.CharField(
        write_only=True, required=True, label='Contraseña'
    )
    password2 = serializers.CharField(
        write_only=True, required=True, label='Confirmar contraseña'
    )

    # --- Campos del Profile (¡AÑADIMOS write_only=True!) ---
    control_number = serializers.CharField(
        required=True, label='Número de Control', write_only=True
    )
    career = serializers.CharField(
        required=True, label='Carrera', write_only=True
    )
    phone_number = serializers.CharField(
        required=True, label='Número de Teléfono', write_only=True
    )
    date_of_birth = serializers.DateField(
        required=True, label='Fecha de Nacimiento', write_only=True
    )
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'username',
            'email',
            'password', 
            'password2',
            # Campos del perfil
            'control_number',
            'career',
            'phone_number',
            'date_of_birth'
        ]

    # ... (tus métodos 'validate' y 'create' se quedan exactamente igual) ...
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return data

    def create(self, validated_data):
        # ... (todo tu código de 'create' se queda igual) ...
        
        # 1. Sacamos los datos del perfil
        profile_data = {
            'control_number': validated_data.pop('control_number'),
            'career': validated_data.pop('career'),
            'phone_number': validated_data.pop('phone_number'),
            'date_of_birth': validated_data.pop('date_of_birth')
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
            from apps.audits.models import AuditLog
            AuditLog.objects.create(
                user=user,
                action='USER_REGISTERED',
                details=f"Nuevo usuario registrado: '{user.username}' (ID: {user.id})"
            )
        except ImportError:
            pass

        return user
from django.db import models
from django.contrib.auth.models import User
# Importa las señales para la creación automática
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """
    Modelo de Perfil extendido para el Usuario.
    Aquí manejamos roles y el estatus de aprobación del vendedor.
    """
    
    # Relación uno-a-uno con el modelo User de Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # --- Roles de Usuario ---
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('vendor', 'Vendedor'),
        ('client', 'Cliente'),
    ]
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='client', # Todos los nuevos usuarios son clientes por defecto
        verbose_name='Rol'
    )

    # --- Estatus de Vendedor (para aprobación de Admins) ---
    VENDOR_STATUS_CHOICES = [
        ('pending', 'Pendiente de Aprobación'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]
    vendor_status = models.CharField(
        max_length=10, 
        choices=VENDOR_STATUS_CHOICES, 
        null=True, 
        blank=True, # Solo es relevante si alguien solicita ser vendedor
        verbose_name='Estatus de Vendedor'
    )

    # --- Otros campos opcionales del perfil ---
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono')
    store_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nombre de Tienda')
    control_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='No. Control')
    career = models.CharField(max_length=100, blank=True, null=True, verbose_name='Carrera')
    date_of_birth = models.DateField(blank=True, null=True, verbose_name='Fecha de Nacimiento')

    profile_image = models.ImageField(
        upload_to='profiles/',  # Guarda las imágenes en la carpeta 'media/profiles/'
        null=True, 
        blank=True, 
        verbose_name='Foto de Perfil'
    )
    is_banned = models.BooleanField(default=False, verbose_name='Está Baneado')
    ban_reason = models.TextField(
        blank=True, 
        null=True, 
        verbose_name='Razón de Baneo'
    )

    def __str__(self):
        return f'Perfil de {self.user.username} ({self.get_role_display()})'

# --- Señales (Signals) para la magia automática ---
# Estas funciones crean un Profile automáticamente cada vez que un User se registra.

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
# En: apps/audits/models.py

from django.db import models
from django.contrib.auth.models import User

class AuditLog(models.Model):
    """
    Modelo para la Bitácora de Auditoría.
    Registra acciones clave realizadas en el sistema.
    """
    
    # --- Definición de Acciones ---
    # (Podemos añadir más después)
    ACTION_CHOICES = [
        # Acciones de Admin
        ('VENDOR_APPROVED', 'Vendedor Aprobado'),
        ('VENDOR_REJECTED', 'Vendedor Rechazado'),
        ('PRODUCT_APPROVED', 'Producto Aprobado'),
        ('PRODUCT_REJECTED', 'Producto Rechazado'),
        ('ORDER_STATUS_CHANGED', 'Estado de Pedido Cambiado'),
        
        # Acciones de Usuario
        ('USER_REGISTERED', 'Usuario Registrado'),
        ('USER_LOGIN', 'Inicio de Sesión'),
        ('PRODUCT_CREATED', 'Producto Creado'),
        ('ORDER_CREATED', 'Pedido Creado'),
    ]

    # --- Campos del Modelo ---
    
    # QUIÉN: El usuario que realizó la acción.
    # (Puede ser null si la acción fue del sistema o un usuario anónimo)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Usuario'
    )
    
    # QUÉ: El tipo de acción realizada.
    action = models.CharField(
        max_length=50, 
        choices=ACTION_CHOICES,
        verbose_name='Acción'
    )
    
    # DETALLES: Texto libre para detalles específicos
    # (Ej. "Admin 'admin' cambió Pedido #101 de 'Pagado' a 'Enviado'")
    details = models.TextField(blank=True, null=True, verbose_name='Detalles')
    
    # CUÁNDO: La fecha y hora de la acción.
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora')

    def __str__(self):
        user_str = self.user.username if self.user else 'Sistema'
        return f'[{self.timestamp.strftime("%Y-%m-%d %H:%M")}] {user_str}: {self.get_action_display()}'

    class Meta:
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-timestamp'] # Mostrar los más recientes primero
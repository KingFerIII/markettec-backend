# En: apps/products/models.py

from django.db import models
# Importamos el Profile de la app 'users' para enlazar el producto con un vendedor
from apps.users.models import Profile 

class Category(models.Model):
    """
    Modelo para categorías de productos (ej. Electrónica, Ropa, etc.)
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    description = models.TextField(blank=True, null=True, verbose_name='Descripción')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'


class Product(models.Model):
    """
    Modelo para los productos del marketplace.
    """
    
    # --- Estados de Moderación (Clave para tu proyecto) ---
    STATUS_CHOICES = [
        ('pending', 'Pendiente de Revisión'), # Enviado por el vendedor
        ('active', 'Activo'),                # Aprobado por el admin
        ('rejected', 'Rechazado'),             # Rechazado por el admin
        ('archived', 'Archivado'),           # Ocultado por el vendedor
    ]

    name = models.CharField(max_length=255, verbose_name='Nombre del Producto')
    description = models.TextField(verbose_name='Descripción')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio')
    inventory = models.PositiveIntegerField(default=0, verbose_name='Inventario')
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='active', # ¡Los productos nuevos siempre entran como pendientes!
        verbose_name='Estatus'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')

    # --- Relaciones Clave ---
    
    # Relación con el Vendedor (un Profile con rol 'vendor')
    vendor = models.ForeignKey(
        Profile, 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name='Vendedor'
        # Opcional: Limitar a solo perfiles que sean vendedores
        # limit_choices_to={'role': 'vendor'} 
    )
    
    # Relación con Categoría
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, # Si se borra la categoría, el producto no se borra
        null=True, 
        blank=True, 
        related_name='products',
        verbose_name='Categoría'
    )

    def __str__(self):
        return f'{self.name} ({self.get_status_display()})'

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
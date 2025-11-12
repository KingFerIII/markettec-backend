# En: apps/products/models.py

from django.db import models
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
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente de Revisión'),
        ('active', 'Activo'),
        ('rejected', 'Rechazado'),
    ]

    name = models.CharField(max_length=255, verbose_name='Nombre del Producto')
    description = models.TextField(verbose_name='Descripción')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio')
    inventory = models.PositiveIntegerField(default=0, verbose_name='Inventario')
    
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='active', # Los productos se publican al instante
        verbose_name='Estatus'
    )
    
    # --- ¡CAMPO NUEVO AÑADIDO! ---
    product_image = models.ImageField(
        upload_to='products/',  # Guarda las imágenes en la carpeta 'media/products/'
        null=True, 
        blank=True, 
        verbose_name='Imagen del Producto'
    )
    # ---------------------------
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')

    # --- Relaciones Clave ---
    vendor = models.ForeignKey(
        Profile, 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name='Vendedor'
    )
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
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
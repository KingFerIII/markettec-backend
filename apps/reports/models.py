# En: apps/reports/models.py

from django.db import models
from apps.users.models import Profile
from apps.products.models import Product

class Report(models.Model):
    """
    Modelo para un reporte hecho por un usuario sobre un producto.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),  # El admin no lo ha visto
        ('resolved', 'Resuelto'),  # El admin ya tomó una decisión (ej. borró el producto)
    ]

    # Quién hizo el reporte
    reporter = models.ForeignKey(
        Profile, 
        on_delete=models.SET_NULL, # Si se borra el perfil del reportante, el reporte queda
        null=True,
        related_name='reports_made',
        verbose_name='Reportante'
    )
    
    # Qué producto fue reportado
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, # Si se borra el producto, se borra el reporte
        related_name='reports',
        verbose_name='Producto'
    )
    
    reason = models.TextField(verbose_name='Razón del Reporte')
    
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending', 
        verbose_name='Estatus'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha del Reporte')

    def __str__(self):
        # Asegurarnos de que el username exista
        reporter_name = self.reporter.user.username if self.reporter and self.reporter.user else 'Usuario Eliminado'
        product_name = self.product.name if self.product else 'Producto Eliminado'
        return f"Reporte de {reporter_name} sobre {product_name}"
    
    class Meta:
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering = ['-created_at']
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
        ('resolved', 'Resuelto'),  # El admin ya tomó una decisión
    ]

    # Quién hizo el reporte
    reporter = models.ForeignKey(
        Profile, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='reports_made',
        verbose_name='Reportante'
    )
    
    # Qué producto fue reportado
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='reports',
        verbose_name='Producto'
    )
    
    reason = models.TextField(verbose_name='Razón del Reporte')
    
    # --- ¡NUEVO CAMPO! ---
    # Para subir capturas de pantalla o fotos de evidencia
    evidence = models.ImageField(
        upload_to='reports/evidence/', 
        blank=True, 
        null=True, 
        verbose_name='Evidencia (Captura)'
    )
    # ---------------------
    
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending', 
        verbose_name='Estatus'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha del Reporte')

    def __str__(self):
        reporter_name = self.reporter.user.username if self.reporter and self.reporter.user else 'Usuario Eliminado'
        product_name = self.product.name if self.product else 'Producto Eliminado'
        return f"Reporte de {reporter_name} sobre {product_name}"
    
    class Meta:
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering = ['-created_at']
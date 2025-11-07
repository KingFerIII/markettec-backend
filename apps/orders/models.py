# En: apps/orders/models.py

from django.db import models
from apps.users.models import Profile
from apps.products.models import Product

class Order(models.Model):
    """
    Modelo para el pedido (la orden completa).
    """
    
    # --- Estados del Pedido ---
    STATUS_CHOICES = [
        ('pending_payment', 'Pendiente de Pago'),
        ('paid', 'Pagado'), # <-- La app Android pone este estado
        ('sent', 'Enviado'), # <-- El Admin web pone este estado
        ('delivered', 'Entregado'), # <-- El Admin web pone este estado
        ('canceled', 'Cancelado'), # <-- Admin o Cliente
    ]

    # Relación con el Cliente
    client = models.ForeignKey(
        Profile, 
        on_delete=models.SET_NULL, # Si el perfil se borra, el pedido NO se borra
        null=True, 
        related_name='orders',
        verbose_name='Cliente'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending_payment',
        verbose_name='Estatus'
    )
    
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        verbose_name='Precio Total'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')

    # ... otros campos: dirección de envío, método de pago, etc.

    def __str__(self):
        return f'Pedido #{self.id} - {self.client} ({self.get_status_display()})'

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at'] # Mostrar los más nuevos primero


class OrderItem(models.Model):
    """
    Modelo para cada artículo dentro de un pedido.
    (Ej. 3 x Camisa Azul, 1 x Pantalón Negro)
    """
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, # Si se borra el pedido, se borran los artículos
        related_name='items',
        verbose_name='Pedido'
    )
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.SET_NULL, # Si el producto se borra, el item permanece (historial)
        null=True,
        verbose_name='Producto'
    )
    
    quantity = models.PositiveIntegerField(default=1, verbose_name='Cantidad')
    
    # Guarda el precio al momento de la compra para evitar inconsistencias
    # si el precio del producto cambia después.
    price_at_purchase = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Precio al Comprar'
    )

    def __str__(self):
        return f'{self.quantity} x {self.product.name} @ {self.price_at_purchase}'

    class Meta:
        verbose_name = 'Artículo del Pedido'
        verbose_name_plural = 'Artículos del Pedido'
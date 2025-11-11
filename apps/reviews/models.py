# En: apps/reviews/models.py

from django.db import models
from apps.users.models import Profile
from apps.products.models import Product
from django.core.validators import MinValueValidator, MaxValueValidator

class Review(models.Model):
    """
    Modelo para una reseña (comentario + calificación)
    hecha por un usuario sobre un producto.
    """
    
    # El producto que está siendo reseñado
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, # Si se borra el producto, se borran sus reseñas
        related_name='reviews',
        verbose_name='Producto'
    )
    
    # Quién hizo la reseña
    reviewer = models.ForeignKey(
        Profile, 
        on_delete=models.CASCADE, # Si se borra el perfil, se borran sus reseñas
        related_name='reviews_made',
        verbose_name='Autor de la reseña'
    )
    
    # Calificación (ej. 1 a 5 estrellas)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Calificación (1-5)'
    )
    
    # Comentario escrito
    comment = models.TextField(blank=True, null=True, verbose_name='Comentario')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Reseña')

    class Meta:
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'
        ordering = ['-created_at']
        
        # --- ¡REGLA DE NEGOCIO IMPORTANTE! ---
        # Un usuario solo puede dejar UNA reseña por producto.
        constraints = [
            models.UniqueConstraint(
                fields=['reviewer', 'product'], 
                name='unique_review_per_user_product'
            )
        ]

    def __str__(self):
        reviewer_name = self.reviewer.user.username if self.reviewer and self.reviewer.user else 'N/A'
        return f"Reseña de {reviewer_name} para {self.product.name} ({self.rating} estrellas)"
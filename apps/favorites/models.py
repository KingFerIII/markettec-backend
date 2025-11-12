# En: apps/favorites/models.py

from django.db import models
from apps.users.models import Profile
from apps.products.models import Product

class Favorite(models.Model):
    """
    Modelo para un "Favorito".
    Es una conexión simple entre un usuario y un producto.
    """
    
    # El usuario que dio "favorito"
    profile = models.ForeignKey(
        Profile, 
        on_delete=models.CASCADE, # Si se borra el perfil, se borran sus favoritos
        related_name='favorites',
        verbose_name='Usuario'
    )
    
    # El producto que fue marcado como favorito
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, # Si se borra el producto, se borra el 'favorito'
        related_name='favorited_by',
        verbose_name='Producto'
    )
    
    # Cuándo se marcó
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')

    class Meta:
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        ordering = ['-created_at']
        
        # --- ¡REGLA DE NEGOCIO IMPORTANTE! ---
        # Un usuario no puede 'favoritear' el mismo producto dos veces.
        constraints = [
            models.UniqueConstraint(
                fields=['profile', 'product'], 
                name='unique_favorite_per_user_product'
            )
        ]

    def __str__(self):
        profile_name = self.profile.user.username if self.profile and self.profile.user else 'Usuario Eliminado'
        product_name = self.product.name if self.product else 'Producto Eliminado'
        return f"{profile_name} marcó como favorito a {product_name}"
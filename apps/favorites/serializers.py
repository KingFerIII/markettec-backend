# En: apps/favorites/serializers.py

from rest_framework import serializers
from .models import Favorite
from apps.products.models import Product
from apps.products.serializers import ProductSerializer # Para anidar

class FavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer para MOSTRAR la lista de favoritos.
    Muestra el producto completo anidado.
    """
    # Anidamos el serializer del producto para mostrar todos sus detalles
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = [
            'id', # El ID del 'favorito' (para poder borrarlo)
            'product'
        ]


class FavoriteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para CREAR un favorito.
    Solo acepta el ID del producto.
    """
    
    # Hacemos que 'product' sea un campo de solo escritura que espera un ID
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )

    class Meta:
        model = Favorite
        fields = ['product'] # Solo pedimos el producto

    def validate(self, data):
        """
        Validaciones personalizadas antes de crear.
        """
        product = data.get('product')
        # Obtenemos el perfil del usuario desde la 'vista'
        profile = self.context['request'].user.profile

        # Validación 1: No puedes favoritear tu propio producto
        if product.vendor == profile:
            raise serializers.ValidationError("No puedes marcar tu propio producto como favorito.")
        
        # Validación 2: No puedes favoritearlo dos veces (la DB también lo valida)
        if Favorite.objects.filter(product=product, profile=profile).exists():
            raise serializers.ValidationError("Este producto ya está en tus favoritos.")
            
        return data

    def create(self, validated_data):
        # Asignamos el 'profile' (dueño) automáticamente desde el request
        profile = self.context['request'].user.profile
        
        favorite = Favorite.objects.create(
            profile=profile,
            product=validated_data.get('product')
        )
        return favorite
# En: apps/products/serializers.py

from rest_framework import serializers
from .models import Product, Category
# Importamos el serializer PÚBLICO que creamos
from apps.users.serializers import PublicProfileSerializer 

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image']


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer principal para el Producto.
    (Actualizado para incluir la imagen)
    """
    
    # Usamos el serializer público para no exponer datos privados
    vendor = PublicProfileSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 
            'name', 
            'description', 
            'price', 
            'inventory', 
            'status', 
            'vendor', 
            'category', 
            'category_name',
            'product_image' # <-- ¡CAMPO NUEVO AÑADIDO!
        ]
        
        # El 'status' es 'read_only' porque es automático (default='active')
        read_only_fields = ['status', 'vendor']
        
        extra_kwargs = {
            'category': {'write_only': True}
        }
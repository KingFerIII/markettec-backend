# En: apps/products/serializers.py

from rest_framework import serializers
from .models import Product, Category
from apps.users.serializers import ProfileSerializer # Para mostrar info del vendedor
from apps.users.serializers import PublicProfileSerializer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer principal para el Producto.
    """
    
    # Anidamos el perfil del vendedor para mostrar sus datos
    # Usamos read_only=True porque este campo se asignará automáticamente
    vendor = PublicProfileSerializer(read_only=True)
    
    # Mostramos el nombre de la categoría, no solo el ID
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
            'vendor', # El perfil anidado
            'category', # El ID de la categoría (para escribir)
            'category_name' # El nombre (para leer)
        ]
        
        # --- Reglas de la API ---
        read_only_fields = [
            'status', # El admin lo controla desde el /admin/, no el vendedor
            'vendor'  # Se asigna automáticamente
        ]
        
        # Hacemos 'category' de solo escritura (write_only)
        # porque ya mostramos 'category_name' para lectura.
        extra_kwargs = {
            'category': {'write_only': True}
        }
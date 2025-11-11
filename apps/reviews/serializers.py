# En: apps/reviews/serializers.py

from rest_framework import serializers
from .models import Review
from apps.users.serializers import PublicProfileSerializer # Para mostrar info del autor

class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer para leer y crear Reseñas.
    """
    
    # --- Campo de LECTURA ---
    # Muestra el perfil público del autor de la reseña
    reviewer = PublicProfileSerializer(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 
            'reviewer', # (Para Leer)
            'product',  # (Para Escribir - será un ID)
            'rating', 
            'comment', 
            'created_at'
        ]
        
        # El 'reviewer' se asigna automáticamente, no se envía en el JSON
        read_only_fields = ('reviewer',)

    def validate(self, data):
        """
        Validación extra: Asegura que el usuario no reseñe su propio producto.
        """
        # Obtenemos el perfil del usuario que está haciendo la petición
        reviewer_profile = self.context['request'].user.profile
        product = data.get('product')

        if product.vendor == reviewer_profile:
            raise serializers.ValidationError("No puedes dejar una reseña en tu propio producto.")
        
        return data

    def create(self, validated_data):
        # Asignamos el autor (el usuario logueado)
        reviewer_profile = self.context['request'].user.profile
        
        # Creamos la reseña
        review = Review.objects.create(
            reviewer=reviewer_profile,
            **validated_data
        )
        return review
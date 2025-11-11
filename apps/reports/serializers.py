# En: apps/reports/serializers.py

from rest_framework import serializers
from .models import Report
from apps.users.serializers import PublicProfileSerializer # Para mostrar info del reportante
from apps.products.serializers import ProductSerializer # Para mostrar info del producto

class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer para LEER y CREAR reportes.
    """
    
    # --- Campos de LECTURA (para el Admin) ---
    # Mostramos los perfiles anidados para que el admin tenga contexto
    reporter = PublicProfileSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    
    # --- Campo de ESCRITURA (para el Usuario) ---
    # Al crear, el usuario solo necesita enviar el ID del producto
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 
            'reporter', # (Leer)
            'product',  # (Leer)
            'product_id', # (Escribir)
            'reason', 
            'status', 
            'created_at',
        ]
        
        # El 'status' solo lo puede cambiar el Admin (lo manejaremos en la Vista)
        read_only_fields = ('reporter', 'status',)

    def create(self, validated_data):
        # Asignamos el reportante automáticamente (el usuario logueado)
        reporter_profile = self.context['request'].user.profile
        
        # Creamos el reporte
        report = Report.objects.create(
            reporter=reporter_profile,
            **validated_data
        )
        return report
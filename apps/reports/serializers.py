# En: apps/reports/serializers.py

from rest_framework import serializers
from .models import Report
from apps.users.serializers import PublicProfileSerializer
from apps.products.serializers import ProductSerializer

class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer para LEER y CREAR reportes.
    """
    
    # --- Campos de LECTURA (para el Admin) ---
    reporter = PublicProfileSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    
    # --- Campo de ESCRITURA (para el Usuario) ---
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 
            'reporter', 
            'product', 
            'product_id', 
            'reason', 
            'evidence', # <--- ¡NUEVO CAMPO AÑADIDO!
            'status', 
            'created_at',
        ]
        
        read_only_fields = ('reporter', 'status', 'created_at')

    def create(self, validated_data):
        # Asignamos el reportante automáticamente
        reporter_profile = self.context['request'].user.profile
        
        report = Report.objects.create(
            reporter=reporter_profile,
            **validated_data
        )
        return report
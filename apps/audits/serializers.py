# En: apps/audits/serializers.py
from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    # Muestra el 'username' en lugar del ID de usuario
    user = serializers.StringRelatedField()
    # Muestra el texto legible de la acción (ej. "Vendedor Aprobado")
    action = serializers.CharField(source='get_action_display')

    class Meta:
        model = AuditLog
        fields = ['id', 'timestamp', 'user', 'action', 'details']
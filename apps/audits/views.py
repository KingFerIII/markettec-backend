# En: apps/audits/views.py
from rest_framework import viewsets, permissions
from .models import AuditLog
from .serializers import AuditLogSerializer
from apps.users.permissions import IsAdminUser # ¡Reutilizamos nuestro permiso!

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint de API de SOLO LECTURA para que los Admins
    consulten la bitácora de auditoría.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    
    # ¡Solo los Administradores pueden ver la bitácora!
    permission_classes = [IsAdminUser]
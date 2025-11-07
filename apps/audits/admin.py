# En: apps/audits/admin.py

from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Configuración de Admin de SOLO LECTURA para la bitácora.
    """
    list_display = ('timestamp', 'user', 'action', 'details')
    list_filter = ('action', 'user', 'timestamp')
    search_fields = ('user__username', 'details')
    
    # --- Bloquea toda edición ---
    
    def has_add_permission(self, request):
        # Nadie puede AÑADIR registros desde el admin
        return False

    def has_change_permission(self, request, obj=None):
        # Nadie puede CAMBIAR registros
        return False

    def has_delete_permission(self, request, obj=None):
        # Nadie puede BORRAR registros
        return False
# En: apps/reports/permissions.py

from rest_framework.permissions import BasePermission
from apps.users.permissions import IsAdminUser # ¡Reutilizamos el permiso de Admin!

class IsAdminOrReadOnly(BasePermission):
    """
    Permiso corregido:
    - Admins: Pueden hacer todo.
    - Usuarios Logueados: Pueden CREAR (POST) y VER (GET).
    
    La lógica de 'get_queryset' en la vista se encarga de
    filtrar lo que ven (los no-admins verán una lista vacía).
    """
    
    def has_permission(self, request, view):
        # Si el usuario no está logueado, no puede hacer nada.
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Si la acción es editar, actualizar o borrar, DEBE ser Admin.
        if view.action in ['update', 'partial_update', 'destroy']:
            return IsAdminUser().has_permission(request, view)
        
        # Para 'list' (GET), 'retrieve' (GET /<id>/), y 'create' (POST),
        # solo necesita estar logueado.
        return True
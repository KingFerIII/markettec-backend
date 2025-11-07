# En: apps/users/permissions.py

from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """
    Permite el acceso solo a usuarios administradores.
    """
    message = "Acción no permitida. Solo los administradores pueden realizar esta acción."

    def has_permission(self, request, view):
        # Comprueba que el usuario esté autenticado y tenga un perfil
        if not request.user or not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            return False
        
        # Comprueba que el rol sea 'admin'
        return request.user.profile.role == 'admin'


class IsOwnerOrAdmin(BasePermission):
    """
    Permite el acceso al dueño del objeto o a un administrador.
    (Ideal para el 'detail view' de un perfil: GET, PUT, PATCH)
    """
    message = "No tienes permiso para ver o editar este perfil."

    def has_permission(self, request, view):
        # Solo requerimos que esté autenticado para continuar
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        'obj' es la instancia del modelo 'User' que se está consultando.
        """
        # Si el usuario es admin, tiene permiso
        if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
            return True
        
        # Si el usuario es el dueño del perfil, tiene permiso
        return obj == request.user
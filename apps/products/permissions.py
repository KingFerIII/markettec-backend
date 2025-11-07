# En: apps/products/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.users.permissions import IsAdminUser # Importamos el permiso de Admin

class IsVendorUser(BasePermission):
    """
    Permite el acceso solo a usuarios con rol de Vendedor.
    """
    message = "Solo los vendedores pueden realizar esta acción."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            return False
        return request.user.profile.role == 'vendor'


class IsOwnerOrAdmin(BasePermission):
    """
    Permite el acceso al Admin, o al dueño (Vendedor) del producto.
    Permite acceso de solo lectura (GET, HEAD, OPTIONS) a cualquiera.
    """
    message = "No tienes permiso para editar este producto."

    def has_permission(self, request, view):
        # Permite peticiones seguras (GET, HEAD, OPTIONS) a todos
        if request.method in SAFE_METHODS:
            return True
        
        # Para peticiones no seguras (POST, PUT, PATCH, DELETE),
        # verifica que el usuario esté autenticado.
        return request.user and request.user.is_authenticated and hasattr(request.user, 'profile')

    def has_object_permission(self, request, view, obj):
        """
        'obj' es la instancia del modelo 'Product'.
        """
        # Permite peticiones seguras a todos
        if request.method in SAFE_METHODS:
            return True
            
        # Admin tiene permiso total
        if request.user.profile.role == 'admin':
            return True
        
        # El vendedor dueño del producto ('obj.vendor') puede editar
        return obj.vendor == request.user.profile

class IsOwnerOnly(BasePermission):
    """
    Permite el acceso solo al Vendedor que es dueño del producto.
    No permite acceso al Admin.
    """
    message = "Solo el vendedor dueño de este producto puede realizar esta acción."

    def has_permission(self, request, view):
        # Solo requerimos que esté autenticado para continuar
        return request.user and request.user.is_authenticated and hasattr(request.user, 'profile')

    def has_object_permission(self, request, view, obj):
        """
        'obj' es la instancia del modelo 'Product'.
        Comprueba si el 'vendor' del producto es el perfil del usuario.
        """
        return obj.vendor == request.user.profile
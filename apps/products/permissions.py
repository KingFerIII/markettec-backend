# En: apps/products/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.users.permissions import IsAdminUser 

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
    """
    message = "No tienes permiso para editar este producto."

    def has_permission(self, request, view):
        # 1. Permisos globales: Debe estar autenticado y tener perfil
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and hasattr(request.user, 'profile')

    def has_object_permission(self, request, view, obj):
        # 1. Lectura libre
        if request.method in SAFE_METHODS:
            return True
            
        # 2. Si es Admin, pase VIP
        if request.user.profile.role == 'admin':
            return True
        
        # 3. Validación de Dueño (A PRUEBA DE BALAS)
        # Verificamos que el producto tenga vendedor asignado
        if not hasattr(obj, 'vendor') or not obj.vendor:
            return False

        # COMPARAMOS USER IDs DIRECTAMENTE (Números)
        # Esto evita errores de comparación de objetos Profile
        return obj.vendor.user.id == request.user.id

class IsOwnerOnly(BasePermission):
    """
    Estricto: Solo el dueño.
    """
    message = "Solo el vendedor dueño de este producto puede realizar esta acción."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'profile')

    def has_object_permission(self, request, view, obj):
        if not hasattr(obj, 'vendor') or not obj.vendor:
            return False
            
        # COMPARAMOS USER IDs DIRECTAMENTE
        return obj.vendor.user.id == request.user.id
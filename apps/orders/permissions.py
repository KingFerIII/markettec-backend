# En: apps/orders/permissions.py

from rest_framework.permissions import BasePermission
from apps.users.models import Profile # Importamos Profile para checar roles

class IsOrderOwnerOrAdmin(BasePermission):
    """
    Permite el acceso solo al Admin o al Cliente que es dueño del pedido.
    """
    message = "No tienes permiso para ver este pedido."

    def has_object_permission(self, request, view, obj):
        """
        'obj' es la instancia del modelo 'Order'.
        """
        # Si el usuario es admin, tiene permiso
        if request.user.profile.role == 'admin':
            return True
        
        # Si el 'client' del pedido es el perfil del usuario, tiene permiso
        return obj.client == request.user.profile
# En: apps/favorites/permissions.py

from rest_framework.permissions import BasePermission

class IsFavoriteOwner(BasePermission):
    """
    Permiso personalizado:
    - Solo permite al dueño del favorito (profile) borrarlo.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        'obj' es la instancia de Favorite.
        Se llama solo en 'detail' (GET <id>, PUT, DELETE).
        """
        
        # Comprueba si el 'profile' (dueño) del favorito
        # es el perfil del usuario que hace la petición.
        if not hasattr(request.user, 'profile'):
            return False
        return obj.profile == request.user.profile
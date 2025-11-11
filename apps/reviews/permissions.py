# En: apps/reviews/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsReviewOwnerOrReadOnly(BasePermission):
    """
    Permiso personalizado para las reseñas:
    - Permite a cualquiera leer (GET).
    - Permite a usuarios logueados crear (POST).
    - Permite solo al dueño editar o borrar (PUT/PATCH/DELETE).
    """
    
    def has_permission(self, request, view):
        # Si es un método seguro (GET, HEAD, OPTIONS), todos pueden.
        if request.method in SAFE_METHODS:
            return True
        
        # Para cualquier otro método (POST, PUT, DELETE),
        # el usuario debe estar logueado.
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        'obj' es la instancia de la Reseña (Review).
        Se llama solo para PUT/PATCH/DELETE.
        """
        # Si es un método seguro, todos pueden (aunque ya se cubrió arriba).
        if request.method in SAFE_METHODS:
            return True
        
        # Para editar/borrar, el 'reviewer' (autor) de la reseña
        # debe ser el perfil del usuario que hace la petición.
        return obj.reviewer == request.user.profile
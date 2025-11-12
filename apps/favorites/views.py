# En: apps/favorites/views.py

from rest_framework import viewsets, mixins, permissions
from .models import Favorite
from .serializers import FavoriteSerializer, FavoriteCreateSerializer
from .permissions import IsFavoriteOwner
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['5. Favoritos'])
class FavoriteViewSet(mixins.CreateModelMixin,      # Para 'POST' (Crear)
                   mixins.ListModelMixin,        # Para 'GET' (Listar)
                   mixins.DestroyModelMixin,     # Para 'DELETE' (Borrar)
                   viewsets.GenericViewSet):
    """
    API Endpoint para Favoritos.
    - GET /api/favorites/: Devuelve la lista de favoritos del usuario logueado.
    - POST /api/favorites/: Marca un producto como favorito.
    - DELETE /api/favorites/<id>/: Quita un producto de favoritos.
    """
    
    queryset = Favorite.objects.all()
    # 'permission_classes' y 'serializer_class' se manejan dinámicamente abajo

    def get_permissions(self):
        """
        Asigna los permisos correctos dependiendo de la acción.
        """
        if self.action == 'destroy':
            # Para BORRAR, debe ser el dueño (IsFavoriteOwner)
            return [permissions.IsAuthenticated(), IsFavoriteOwner()]
        
        # Para CREAR o LISTAR, solo necesita estar logueado
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        """
        Elige el serializer correcto.
        Usa FavoriteCreateSerializer para 'POST' (crear).
        Usa FavoriteSerializer para 'GET' (listar).
        """
        if self.action == 'create':
            return FavoriteCreateSerializer
        return FavoriteSerializer

    def get_queryset(self):
        """
        Este es el filtro clave.
        Asegura que la lista SÓLO muestre los favoritos
        del usuario que está haciendo la petición.
        """
        # (El permiso ya se aseguró de que el usuario está logueado)
        profile = self.request.user.profile
        
        # Filtra la base de datos por el perfil del usuario
        return Favorite.objects.filter(profile=profile)

    def get_serializer_context(self):
        """
        Pasa el 'request' al serializer.
        (Es OBLIGATORIO para que el FavoriteCreateSerializer
        sepa quién es el usuario logueado)
        """
        return {'request': self.request}
from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Favorite
from .serializers import FavoriteSerializer, FavoriteCreateSerializer
from .permissions import IsFavoriteOwner
from apps.products.models import Product
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

@extend_schema(tags=['5. Favoritos'])
class FavoriteViewSet(mixins.CreateModelMixin,      # Para 'POST' (Crear tradicional)
                   mixins.ListModelMixin,        # Para 'GET' (Listar)
                   mixins.DestroyModelMixin,     # Para 'DELETE' (Borrar tradicional)
                   viewsets.GenericViewSet):
    """
    API Endpoint para Favoritos.
    - GET /api/favorites/: Devuelve la lista de favoritos del usuario logueado.
    - POST /api/favorites/toggle/: (NUEVO) Agrega/Quita favorito enviando product_id.
    - DELETE /api/favorites/<id>/: Quita un producto de favoritos (método viejo).
    """
    
    queryset = Favorite.objects.all()
    # 'permission_classes' y 'serializer_class' se manejan dinámicamente abajo

    def get_permissions(self):
        """
        Asigna los permisos correctos dependiendo de la acción.
        """
        if self.action == 'destroy':
            # Para BORRAR por ID, debe ser el dueño
            return [permissions.IsAuthenticated(), IsFavoriteOwner()]
        
        # Para CREAR, LISTAR o TOGGLE, solo necesita estar logueado
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        """
        Elige el serializer correcto.
        """
        if self.action == 'create':
            return FavoriteCreateSerializer
        return FavoriteSerializer

    def get_queryset(self):
        """
        Filtra la lista SÓLO para el usuario logueado.
        """
        if getattr(self, 'swagger_fake_view', False):
            # Esto evita un error raro al generar la documentación
            return Favorite.objects.none()

        profile = self.request.user.profile
        return Favorite.objects.filter(profile=profile)

    def get_serializer_context(self):
        """
        Pasa el 'request' al serializer.
        """
        return {'request': self.request}

    # ==========================================
    #  ¡LA SOLUCIÓN PARA ARMANDO (TOGGLE)!
    # ==========================================
    @extend_schema(
        summary="Alternar Favorito (Toggle)",
        description="Envía el ID del producto. Si ya es favorito, lo borra. Si no, lo agrega.",
        request=None, # No requerimos un serializer complejo, solo un JSON simple
        responses={200: None, 201: None},
        parameters=[
            OpenApiParameter(
                name='product_id', 
                type=OpenApiTypes.INT, 
                location=OpenApiParameter.QUERY, 
                description='ID del producto a alternar (puede ir en query o body)'
            )
        ]
    )
    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle_favorite(self, request):
        # 1. Obtenemos el ID del producto (del JSON o de la URL)
        product_id = request.data.get('product_id') or request.query_params.get('product_id')
        profile = request.user.profile

        if not product_id:
            return Response(
                {"error": "Se requiere el campo 'product_id'"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Buscamos si ya existe este favorito para este usuario
        favorite = Favorite.objects.filter(profile=profile, product_id=product_id).first()

        if favorite:
            # SI YA EXISTE -> LO BORRAMOS (Delete)
            favorite.delete()
            return Response(
                {"status": "deleted", "message": "Eliminado de favoritos", "is_favorite": False}, 
                status=status.HTTP_200_OK
            )
        else:
            # SI NO EXISTE -> LO CREAMOS (Create)
            product = get_object_or_404(Product, id=product_id)
            Favorite.objects.create(profile=profile, product=product)
            return Response(
                {"status": "created", "message": "Agregado a favoritos", "is_favorite": True}, 
                status=status.HTTP_201_CREATED
            )
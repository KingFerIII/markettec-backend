# En: apps/products/views.py

from rest_framework import viewsets, permissions, status, response
from rest_framework.decorators import action

# --- ¡AÑADIMOS 'Avg' PARA CALCULAR PROMEDIOS! ---
from django.db.models import Avg 

from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from .permissions import IsOwnerOrAdmin, IsOwnerOnly
from apps.users.permissions import IsAdminUser
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['3. Productos y Categorías'])
class CategoryViewSet(viewsets.ModelViewSet):
    # ... (Tu CategoryViewSet se queda igual) ...
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsAdminUser] 
        return [permission() for permission in permission_classes]

@extend_schema(tags=['3. Productos y Categorías'])
class ProductViewSet(viewsets.ModelViewSet):
    """
    Endpoint de API para Productos (Modelo Marketplace Abierto).
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        """ Asigna permisos basados en la acción. """
        
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
            
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated] 
            
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrAdmin]

        elif self.action == 'mark_out_of_stock':
            permission_classes = [IsOwnerOnly]

        elif self.action == 'my_publications':
            permission_classes = [permissions.IsAuthenticated]
        
        # --- ¡NUEVA REGLA AÑADIDA! ---
        elif self.action == 'featured':
            permission_classes = [permissions.AllowAny] # Es un endpoint público
            
        else:
            permission_classes = [permissions.IsAdminUser] 

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """ Filtra los productos que se muestran en la API. """
        user = self.request.user
        
        if user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'admin':
            return Product.objects.all()

        if user.is_authenticated and hasattr(user, 'profile'):
            return Product.objects.filter(status='active') | Product.objects.filter(vendor=user.profile)

        return Product.objects.filter(status='active')

    def perform_create(self, serializer):
        """ Asigna el 'vendor' (dueño) automáticamente. """
        serializer.save(vendor=self.request.user.profile)
        
    # (Esta función 'update' la borramos en el paso anterior, ¡bien!)

    @extend_schema(tags=['3. Productos y Categorías'], summary="Marcar Agotado")
    @action(detail=True, methods=['post'])
    def mark_out_of_stock(self, request, pk=None):
        """ Endpoint para marcar un producto como 'Agotado'. """
        # ... (Tu código de mark_out_of_stock se queda igual) ...
        try:
            product = self.get_object() 
        except Product.DoesNotExist:
            return response.Response(
                {'error': 'Producto no encontrado.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        product.inventory = 0
        product.save()
        serializer = self.get_serializer(product)
        return response.Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(tags=['3. Productos y Categorías'], summary="Mis Publicaciones")
    @action(detail=False, methods=['get'])
    def my_publications(self, request):
        """ Endpoint para ver 'Mis Publicaciones'. """
        # ... (Tu código de my_publications se queda igual) ...
        products = Product.objects.filter(vendor=self.request.user.profile)
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(products, many=True)
        return response.Response(serializer.data)

    # --- ¡NUEVO ENDPOINT AÑADIDO AL FINAL! ---
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Endpoint público para obtener los productos destacados.
        Devuelve el Top 5 de productos con mejor rating (promedio de estrellas).
        URL: GET /api/products/featured/
        """
        
        # 1. Calculamos el rating promedio de CADA producto
        #    'reviews' es el 'related_name' del Producto en el modelo Review
        #    'reviews__rating' accede al campo 'rating' de la reseña
        featured_products = Product.objects.filter(status='active').annotate(
            average_rating=Avg('reviews__rating')
        ).filter(average_rating__isnull=False).order_by('-average_rating') 
        #    .filter(average_rating__isnull=False) -> (ignora productos sin reseñas)
        #    .order_by('-average_rating') -> (Ordena de mayor a menor)
        
        # 2. Nos quedamos solo con los Top 5
        top_products = featured_products[:5]

        # 3. Serializamos y devolvemos
        serializer = self.get_serializer(top_products, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)
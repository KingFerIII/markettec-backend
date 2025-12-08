from rest_framework import viewsets, permissions, status, response
from rest_framework.decorators import action

# --- IMPORTACIONES CLAVE ---
from django.db.models import Avg, Q 
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from .permissions import IsOwnerOrAdmin, IsOwnerOnly
from apps.users.permissions import IsAdminUser

@extend_schema(tags=['3. Productos y Categorías'])
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsAdminUser] 
        return [permission() for permission in permission_classes]

@extend_schema(
    tags=['3. Productos y Categorías'],
    parameters=[
        OpenApiParameter(
            name='q',
            # ¡OJO AQUÍ! Debe ser STR, no STRING
            type=OpenApiTypes.STR, 
            location=OpenApiParameter.QUERY,
            description='Búsqueda por nombre, descripción o categoría (ej. ?q=iphone)'
        )
    ]
)
class ProductViewSet(viewsets.ModelViewSet):
    """
    Endpoint de API para Productos (Modelo Marketplace Abierto).
    Soporta búsqueda con ?q=texto
    """
    queryset = Product.objects.select_related('category', 'vendor', 'vendor__user').all()
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
            # CAMBIO: Usamos IsOwnerOrAdmin para que no sea tan restrictivo
            permission_classes = [IsOwnerOrAdmin]

        elif self.action == 'my_publications':
            permission_classes = [permissions.IsAuthenticated]
        
        elif self.action == 'featured':
            permission_classes = [permissions.AllowAny]
            
        else:
            permission_classes = [permissions.IsAdminUser] 

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """ 
        Filtra los productos y maneja la búsqueda (?q=).
        """
        user = self.request.user
        
        queryset = Product.objects.select_related('category', 'vendor', 'vendor__user')

        if user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'admin':
            queryset = queryset.all()
        elif user.is_authenticated and hasattr(user, 'profile'):
            queryset = queryset.filter(Q(status='active') | Q(vendor=user.profile))
        else:
            queryset = queryset.filter(status='active')

        # Filtro de Búsqueda Global
        query = self.request.query_params.get('q', None)
        
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user.profile)

    @extend_schema(summary="Marcar Agotado")
    @action(detail=True, methods=['post'])
    def mark_out_of_stock(self, request, pk=None):
        try:
            product = self.get_object() 
        except Product.DoesNotExist:
            return response.Response({'error': 'Producto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
        product.inventory = 0
        product.save()
        serializer = self.get_serializer(product)
        return response.Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(summary="Mis Publicaciones")
    @action(detail=False, methods=['get'])
    def my_publications(self, request):
        products = Product.objects.filter(vendor=self.request.user.profile)
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(products, many=True)
        return response.Response(serializer.data)

    @extend_schema(summary="Productos Destacados")
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_products = Product.objects.filter(status='active').annotate(
            average_rating=Avg('reviews__rating')
        ).filter(average_rating__isnull=False).order_by('-average_rating')
        
        top_products = featured_products[:5]
        serializer = self.get_serializer(top_products, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)
# En: apps/products/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from apps.users.permissions import IsAdminUser

# --- Importamos los permisos correctos ---
# (¡Ya no se usa IsVendorUser!)
from .permissions import IsOwnerOrAdmin, IsOwnerOnly 

class CategoryViewSet(viewsets.ModelViewSet):
    """
    Endpoint de API para Categorías.
    - Cualquiera: Puede LISTAR y VER (GET).
    - Admins: Pueden CREAR (POST), EDITAR (PUT) y BORRAR (DELETE).
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        """ Asigna permisos basados en la acción. """
        
        if self.action in ['list', 'retrieve']:
            # Cualquiera puede ver la lista o el detalle
            permission_classes = [permissions.AllowAny]
        else:
            # Para 'create', 'update', 'partial_update', 'destroy'
            # solo los admins pueden
            permission_classes = [IsAdminUser] 
            
        return [permission() for permission in permission_classes]


class ProductViewSet(viewsets.ModelViewSet):
    """
    Endpoint de API para Productos (Modelo Marketplace Abierto).
    - Cualquiera: Puede LISTAR y VER (GET) productos 'activos'.
    - Usuario Logueado: Puede CREAR (POST) productos.
    - Dueño: Puede EDITAR, BORRAR y MARCAR COMO AGOTADO.
    - Admin: Puede EDITAR y BORRAR.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        """ Asigna permisos basados en la acción. """
        
        if self.action in ['list', 'retrieve']:
            # Cualquiera puede ver la lista o el detalle
            permission_classes = [permissions.AllowAny]
            
        elif self.action == 'create':
            # --- ¡CAMBIO IMPORTANTE! ---
            # Cualquier usuario logueado puede crear un producto
            permission_classes = [permissions.IsAuthenticated] 
            
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Admin o Dueño pueden editar/borrar
            permission_classes = [IsOwnerOrAdmin]

        elif self.action == 'mark_out_of_stock':
            # Solo el Dueño (Vendedor) puede marcar como agotado
            permission_classes = [IsOwnerOnly]

        elif self.action == 'my_publications':
            # Solo un usuario logueado puede ver sus publicaciones
            permission_classes = [permissions.IsAuthenticated]
            
        else:
            permission_classes = [permissions.IsAdminUser] # Seguridad por defecto

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filtra los productos que se muestran en la API.
        """
        user = self.request.user
        
        # Si el usuario es Admin, puede ver todo (incluyendo pendientes/rechazados)
        if user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'admin':
            return Product.objects.all()

        # --- ¡LÓGICA SIMPLIFICADA! ---
        # Si el usuario está logueado (sea quien sea),
        # puede ver SUS productos (de cualquier estado) + los 'activos' de otros.
        if user.is_authenticated and hasattr(user, 'profile'):
            return Product.objects.filter(status='active') | Product.objects.filter(vendor=user.profile)

        # Clientes y usuarios no autenticados solo ven productos 'activos'
        return Product.objects.filter(status='active')

    def perform_create(self, serializer):
        """
        Asigna el 'vendor' (dueño) automáticamente al crear un producto.
        """
        serializer.save(vendor=self.request.user.profile)

    # --- ENDPOINT PARA "MARCAR COMO AGOTADO" ---
    @action(detail=True, methods=['post'])
    def mark_out_of_stock(self, request, pk=None):
        """
        Endpoint para marcar un producto como 'Agotado' (inventario a 0).
        URL: POST /api/products/<id>/mark_out_of_stock/
        """
        try:
            product = self.get_object() 
        except Product.DoesNotExist:
            return Response(
                {'error': 'Producto no encontrado.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Lógica de negocio
        product.inventory = 0
        product.save()

        serializer = self.get_serializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # --- ¡NUEVO ENDPOINT PARA "MIS PUBLICACIONES"! ---
    @action(detail=False, methods=['get'])
    def pending_review(self, request):
        """
        Endpoint solo para Admins.
        Devuelve una lista de productos con estado 'pending'.
        URL: GET /api/products/pending_review/
        """
        # (El permiso 'IsAdminUser' ya protegió esta acción)
        
        # Filtramos productos que están 'pendientes'
        pending_products = Product.objects.filter(status='pending')
        
        # Paginamos los resultados (buena práctica)
        page = self.paginate_queryset(pending_products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(pending_products, many=True)
        return Response(serializer.data)
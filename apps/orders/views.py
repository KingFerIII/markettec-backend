# En: apps/orders/views.py

from rest_framework import viewsets, mixins, permissions, status 
from rest_framework.decorators import action 
from rest_framework.response import Response 
from .models import Order, OrderItem 
from .serializers import OrderSerializer
from .permissions import IsOrderOwnerOrAdmin
from apps.users.permissions import IsAdminUser 
from apps.audits.models import AuditLog 
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['6. Pedidos'])
class OrderViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    Endpoint de API para Pedidos:
    - POST: Crear un nuevo pedido (solo Clientes).
    - GET (List): Ver mis pedidos (solo Clientes).
    - GET (my-sales): Ver mis VENTAS (solo Vendedores).
    - GET (Detail): Ver un pedido específico.
    - POST (Cancel): Cancelar un pedido.
    - POST (Mark Delivered): Marcar venta como entregada.
    """
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        """
        Filtra el queryset para que los Clientes solo vean sus
        pedidos (COMPRAS), y los Admins vean todo.
        """
        user = self.request.user

        if not user.is_authenticated:
            return Order.objects.none() 

        if hasattr(user, 'profile') and user.profile.role == 'admin':
            return Order.objects.all().prefetch_related('items__product')
        
        # Por defecto (Clientes), solo mostrar sus propios pedidos (COMPRAS)
        return Order.objects.filter(client=user.profile).prefetch_related('items__product')

    def get_permissions(self):
        """ Asigna permisos basados en la acción. """
        
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]

        # --- AGREGADO: Permisos para las nuevas funciones ---
        elif self.action in ['my_sales', 'mark_delivered']:
            permission_classes = [permissions.IsAuthenticated]
        
        elif self.action == 'cancel_order':
            permission_classes = [permissions.IsAuthenticated, IsOrderOwnerOrAdmin]
        
        else:
            permission_classes = [IsAdminUser] 
            
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        return {'request': self.request}

    # --- CANCELAR ORDEN (Tu código original) ---
    @extend_schema(tags=['6. Pedidos'], summary="Cancelar Orden")
    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        try:
            order = self.get_object() 
        except Exception: # Simplificado para evitar error de importación si no jala el get_object
            return Response({'error': 'Pedido no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if order.status in ['sent', 'delivered', 'canceled']:
            return Response(
                {'error': f"No se puede cancelar un pedido que ya está '{order.get_status_display()}'."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            product = item.product
            if product:
                product.inventory += item.quantity
                product.save()

        order.status = 'canceled'
        order.save()
        
        try:
            AuditLog.objects.create(
                user=request.user, 
                action='ORDER_CANCELED',
                details=f"El usuario '{request.user.username}' canceló el pedido #{order.id}"
            )
        except Exception:
            pass

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ==========================================
    #  NUEVO 1: MIS VENTAS
    # ==========================================
    @extend_schema(summary="Ver Mis Ventas (Vendedor)")
    @action(detail=False, methods=['get'], url_path='my-sales')
    def my_sales(self, request):
        """
        Muestra una lista separada con los pedidos donde TÚ eres el vendedor.
        URL: GET /api/orders/my-sales/
        """
        user = request.user
        if not hasattr(user, 'profile'):
             return Response([], status=200)

        # Buscamos pedidos que contengan productos míos
        sales = Order.objects.filter(
            items__product__vendor=user.profile
        ).distinct().order_by('-created_at')

        # Usamos paginación si está activa, si no, lista directa
        page = self.paginate_queryset(sales)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(sales, many=True)
        return Response(serializer.data)

    # ==========================================
    #  NUEVO 2: MARCAR ENTREGADO
    # ==========================================
    @extend_schema(summary="Marcar como Entregado")
    @action(detail=True, methods=['post'], url_path='mark-delivered')
    def mark_delivered(self, request, pk=None):
        """
        Cambia el estatus a 'delivered'. Solo el vendedor puede hacerlo.
        URL: POST /api/orders/<id>/mark-delivered/
        """
        # Nota: Usamos Order.objects.get porque self.get_object() filtra solo compras
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Pedido no encontrado.'}, status=404)

        # Validación: ¿Soy el vendedor de esto?
        is_vendor = order.items.filter(product__vendor=request.user.profile).exists()
        
        if not is_vendor and not request.user.is_staff:
             return Response({"error": "Solo el vendedor puede entregar este pedido."}, status=403)

        if order.status == 'delivered':
             return Response({"message": "Ya estaba entregado."}, status=200)

        order.status = 'delivered'
        order.save()

        # Bitácora
        try:
            AuditLog.objects.create(
                user=request.user, 
                action='ORDER_DELIVERED',
                details=f"Venta entregada por {request.user.username}"
            )
        except:
            pass

        return Response({"status": "success", "message": "Venta marcada como entregada"}, status=200)
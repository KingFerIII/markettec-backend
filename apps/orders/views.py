# En: apps/orders/views.py

from rest_framework import viewsets, mixins, permissions, status # <-- AÑADIDO status
from rest_framework.decorators import action # <-- AÑADIDO action
from rest_framework.response import Response # <-- AÑADIDO Response
from .models import Order, OrderItem # <-- AÑADIDO OrderItem
from .serializers import OrderSerializer
from .permissions import IsOrderOwnerOrAdmin
from apps.users.permissions import IsAdminUser # <-- AÑADIDO IsAdminUser
from apps.audits.models import AuditLog # Para la bitácora
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
    - GET (Detail): Ver un pedido específico (solo Dueño o Admin).
    - POST (Cancel): Cancelar un pedido (Dueño o Admin).
    """
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        """
        Filtra el queryset para que los Clientes solo vean sus
        pedidos, y los Admins vean todo.
        """
        user = self.request.user

        if not user.is_authenticated:
            return Order.objects.none() 

        if hasattr(user, 'profile') and user.profile.role == 'admin':
            return Order.objects.all().prefetch_related('items__product')
        
        # Por defecto (Clientes), solo mostrar sus propios pedidos
        return Order.objects.filter(client=user.profile).prefetch_related('items__product')

    def get_permissions(self):
        """ Asigna permisos basados en la acción. """
        
        if self.action == 'create':
            # Solo usuarios autenticados (clientes) pueden crear
            permission_classes = [permissions.IsAuthenticated]
        
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        
        # --- ¡NUEVA REGLA! ---
        elif self.action == 'cancel_order':
             # Para ver el detalle o cancelar:
            permission_classes = [permissions.IsAuthenticated, IsOrderOwnerOrAdmin]
        
        else:
            permission_classes = [IsAdminUser] # Seguridad por defecto
            
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        """
        Pasa el objeto 'request' al serializer.
        """
        return {'request': self.request}

    # --- ¡NUEVO ENDPOINT AÑADIDO! ---
    @extend_schema(tags=['6. Pedidos'], summary="Cancelar Orden")
    @action(detail=True, methods=['post'])
    def cancel_order(self, request, pk=None):
        """
        Endpoint para que el dueño o un admin cancelen un pedido
        que no haya sido enviado.
        URL: POST /api/orders/<id>/cancel_order/
        """
        try:
            order = self.get_object() # Obtiene el pedido
        except Order.DoesNotExist:
            return Response(
                {'error': 'Pedido no encontrado.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Lógica de negocio: No se puede cancelar si ya se envió o ya está cancelado
        if order.status in ['sent', 'delivered', 'canceled']:
            return Response(
                {'error': f"No se puede cancelar un pedido que ya está '{order.get_status_display()}'."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- Lógica de Devolución de Inventario ---
        # Buscamos todos los artículos del pedido
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            product = item.product
            # Verificamos que el producto aún exista
            if product:
                # Devolvemos la cantidad al inventario
                product.inventory += item.quantity
                product.save()
        # ----------------------------------------

        # Actualizamos el estado del pedido
        order.status = 'canceled'
        order.save()
        
        # Registrar en la bitácora
        try:
            AuditLog.objects.create(
                user=request.user, 
                action='ORDER_CANCELED',
                details=f"El usuario '{request.user.username}' canceló el pedido #{order.id}"
            )
        except Exception:
            pass # No fallar si la auditoría falla

        # Devolvemos el pedido actualizado
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
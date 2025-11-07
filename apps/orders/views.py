# En: apps/orders/views.py

from rest_framework import viewsets, mixins, permissions
from .models import Order
from .serializers import OrderSerializer
from .permissions import IsOrderOwnerOrAdmin

class OrderViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    Endpoint de API para Pedidos:
    - POST: Crear un nuevo pedido (solo Clientes).
    - GET (List): Ver mis pedidos (solo Clientes).
    - GET (Detail): Ver un pedido específico (solo Dueño o Admin).
    """
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        """
        Filtra el queryset para que los Clientes solo vean sus
        pedidos, y los Admins vean todo.
        """
        user = self.request.user

        if not user.is_authenticated:
            return Order.objects.none() # No mostrar nada si no está logueado

        if user.profile.role == 'admin':
            return Order.objects.all().prefetch_related('items__product')
        
        # Por defecto (Clientes), solo mostrar sus propios pedidos
        return Order.objects.filter(client=user.profile).prefetch_related('items__product')

    def get_permissions(self):
        """ Asigna permisos basados en la acción. """
        
        if self.action == 'create':
            # Solo usuarios autenticados (clientes) pueden crear
            permission_classes = [permissions.IsAuthenticated]
        
        elif self.action in ['list', 'retrieve']:
            # Para ver la lista o el detalle:
            # - 'get_queryset' ya filtra la lista
            # - 'IsOrderOwnerOrAdmin' protege el detalle
            permission_classes = [permissions.IsAuthenticated, IsOrderOwnerOrAdmin]
        
        else:
            permission_classes = [permissions.IsAdminUser] # Seguridad por defecto

        # Corregimos para que IsOrderOwnerOrAdmin solo actúe en 'retrieve'
        if self.action == 'list':
            permission_classes = [permissions.IsAuthenticated]
            
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        """
        Pasa el objeto 'request' al serializer.
        Es necesario para que el serializer sepa qué usuario
        está creando el pedido (self.context['request'].user.profile).
        """
        return {'request': self.request}
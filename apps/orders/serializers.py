# En: apps/orders/serializers.py

from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.models import Product
from apps.products.serializers import ProductSerializer
from apps.audits.models import AuditLog
from apps.users.models import Profile # <--- Importamos Profile para sacar el nombre

# --- 1. NUEVO: SERIALIZER PARA EL CLIENTE (Solo Nombre) ---
class SimpleClientSerializer(serializers.ModelSerializer):
    """
    Muestra solo el ID y el Nombre del cliente.
    """
    # Jalamos el nombre desde el modelo User
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'first_name'] # <--- Solo mostramos esto

# ----------------------------------------------------------

# --- Serializer de LECTURA de items ---
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price_at_purchase']

# --- Serializer de ESCRITURA de items ---
class CreateOrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)

# --- SERIALIZER PRINCIPAL DE LA ORDEN ---
class OrderSerializer(serializers.ModelSerializer):
    # Items (Detalles)
    items = OrderItemSerializer(many=True, read_only=True)
    
    # Input para crear
    items_to_create = CreateOrderItemSerializer(many=True, write_only=True)

    # --- ¡AQUÍ ESTÁ EL CAMBIO! ---
    # Usamos el mini serializer para mostrar el nombre del cliente
    client = SimpleClientSerializer(read_only=True)
    # -----------------------------

    class Meta:
        model = Order
        fields = [
            'id', 
            'client',        # Ahora devolverá { "id": 5, "first_name": "Javi" }
            'status', 
            'total_price', 
            'created_at', 
            'items', 
            'items_to_create'
        ]
        read_only_fields = ['client', 'status', 'total_price']

    def create(self, validated_data):
        items_data = validated_data.pop('items_to_create')
        client_profile = self.context['request'].user.profile
        
        order = Order.objects.create(client=client_profile)
        
        total_order_price = 0

        for item_data in items_data:
            product_id = item_data['product_id']
            quantity = item_data['quantity']
            
            try:
                product = Product.objects.get(id=product_id, status='active')
            except Product.DoesNotExist:
                order.delete()
                raise serializers.ValidationError(f"Producto con id {product_id} no existe o no está activo.")

            if product.inventory < quantity:
                order.delete()
                raise serializers.ValidationError(f"Inventario insuficiente para '{product.name}'. Disponibles: {product.inventory}")
            
            price = product.price
            total_order_price += (price * quantity)
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_purchase=price
            )
            
            product.inventory -= quantity
            product.save()

        order.total_price = total_order_price
        order.save()

        try:
            AuditLog.objects.create(
                user=client_profile.user,
                action='ORDER_CREATED',
                details=f"Nuevo pedido #{order.id} creado. Total: ${order.total_price}"
            )
        except Exception:
            pass
        
        return order
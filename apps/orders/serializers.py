# En: apps/orders/serializers.py

from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.models import Product
from apps.products.serializers import ProductSerializer # Para mostrar detalles
from apps.audits.models import AuditLog

# --- Serializer de LECTURA ---
class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer para LEER los artículos de un pedido.
    Muestra los detalles completos del producto.
    """
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price_at_purchase']


# --- Serializer de ESCRITURA ---
class CreateOrderItemSerializer(serializers.Serializer):
    """
    Serializer para RECIBIR los datos de un artículo
    cuando se crea un pedido.
    """
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer principal para el Pedido.
    Maneja la creación y lectura de pedidos.
    """
    
    # --- Campo de LECTURA ---
    # Muestra los artículos con todos sus detalles (usa el serializer de lectura)
    items = OrderItemSerializer(many=True, read_only=True)
    
    # --- Campo de ESCRITURA ---
    # Recibe una lista de artículos para crear (usa el serializer de escritura)
    items_to_create = CreateOrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 
            'client', 
            'status', 
            'total_price', 
            'created_at', 
            'items', # (Para Leer)
            'items_to_create' # (Para Escribir)
        ]
        read_only_fields = ['client', 'status', 'total_price']

    def create(self, validated_data):
        """
        Sobrescribimos el método 'create' para manejar la creación
        del Pedido y sus Artículos (items) de forma transaccional.
        """
        # 1. Obtenemos los datos de los artículos y el cliente
        items_data = validated_data.pop('items_to_create')
        
        # Obtenemos el perfil del cliente desde el 'contexto' de la vista
        client_profile = self.context['request'].user.profile
        
        # 2. Creamos el Pedido (Order)
        order = Order.objects.create(client=client_profile)
        
        total_order_price = 0

        # 3. Creamos cada Artículo (OrderItem) y calculamos el total
        for item_data in items_data:
            product_id = item_data['product_id']
            quantity = item_data['quantity']
            
            try:
                product = Product.objects.get(id=product_id, status='active')
            except Product.DoesNotExist:
                # Si el producto no existe o no está activo, cancelamos todo
                order.delete() # Borra el pedido que acabamos de crear
                raise serializers.ValidationError(f"Producto con id {product_id} no existe o no está activo.")

            # Validar inventario (¡Opcional pero recomendado!)
            if product.inventory < quantity:
                order.delete()
                raise serializers.ValidationError(f"Inventario insuficiente para '{product.name}'. Disponibles: {product.inventory}")
            
            # Calculamos el precio
            price = product.price
            total_order_price += (price * quantity)
            
            # Creamos el artículo del pedido
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_purchase=price
            )
            
            # Descontamos del inventario
            product.inventory -= quantity
            product.save()

        # 4. Actualizamos el precio total del Pedido
        order.total_price = total_order_price
        order.save()

        # --- ¡CONEXIÓN DE BITÁCORA! ---
        # 5. Creamos el registro de auditoría
        AuditLog.objects.create(
            user=client_profile.user, # Obtenemos el User desde el Profile
            action='ORDER_CREATED',
            details=f"Nuevo pedido #{order.id} creado. Total: ${order.total_price}"
        )
        # --- FIN DE BITÁCORA ---
        
        return order
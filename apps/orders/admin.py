# En: apps/orders/admin.py

from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    """
    Permite ver los 'items' (artículos) DENTRO de la vista del Pedido.
    """
    model = OrderItem
    # Campos que se muestran en la línea del artículo
    fields = ('product', 'quantity', 'price_at_purchase')
    readonly_fields = ('product', 'quantity', 'price_at_purchase')
    extra = 0 # No mostrar formularios de items vacíos
    can_delete = False # No permitir borrar items desde el admin

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Personalización del Admin para gestionar Pedidos.
    """
    list_display = ('id', 'client', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at') # ¡Filtrar por estatus!
    search_fields = ('id', 'client__user__username')
    
    # ¡La clave! Permite cambiar el 'status' desde la lista
    list_editable = ('status',)
    
    # Muestra los OrderItems dentro del detalle del Pedido
    inlines = [OrderItemInline]

    # Definir qué campos se ven y cuáles son de solo lectura
    readonly_fields = ('client', 'total_price', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('client', 'status', 'total_price')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        # Evita que se editen los campos si el pedido ya está creado
        if obj: # 'obj' es la instancia del Pedido
            return self.readonly_fields
        return ()
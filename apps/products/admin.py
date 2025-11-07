# En: apps/products/admin.py

from django.contrib import admin
from .models import Product, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Personalización del Admin para moderar productos.
    """
    list_display = ('name', 'vendor', 'category', 'price', 'inventory', 'status')
    list_filter = ('status', 'category', 'vendor') # ¡Filtros para moderación!
    search_fields = ('name', 'vendor__user__username')
    
    # Permite cambiar el 'status' directamente desde la lista (¡Muy útil!)
    list_editable = ('status', 'price', 'inventory')
    
    # Campos que se muestran al editar un producto
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'status')
        }),
        ('Detalles del Vendedor y Categoría', {
            'fields': ('vendor', 'category')
        }),
        ('Precio e Inventario', {
            'fields': ('price', 'inventory')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',) # Oculta esta sección por defecto
        }),
    )
    
    # Los campos de fecha no deben ser editables
    readonly_fields = ('created_at', 'updated_at')
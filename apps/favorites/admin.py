# En: apps/favorites/admin.py

from django.contrib import admin
from .models import Favorite

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    # Campos que se mostrarán en la lista
    list_display = ('product', 'profile', 'created_at')
    
    # Filtros útiles en el sidebar
    list_filter = ('created_at',)
    
    # Habilitar búsqueda
    search_fields = ('product__name', 'profile__user__username')
    
    # Hacer los campos de solo lectura (un 'favorito' no se debe editar)
    readonly_fields = ('profile', 'product', 'created_at')

    # Desabilitar el botón de "Añadir" 
    # (Los favoritos se crean desde la app, no el admin)
    def has_add_permission(self, request):
        return False
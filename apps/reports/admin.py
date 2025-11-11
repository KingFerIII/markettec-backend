# En: apps/reports/admin.py

from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('product', 'reporter', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('product__name', 'reporter__user__username')
    
    # Hacemos que el admin no pueda editar los detalles del reporte, solo su estado
    readonly_fields = ('reporter', 'product', 'reason', 'created_at')
    
    # Hacemos el 'status' editable desde la lista
    list_editable = ('status',)
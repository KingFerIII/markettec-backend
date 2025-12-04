# En: apps/reports/views.py

from rest_framework import viewsets, mixins, permissions, status, response
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Report
from .serializers import ReportSerializer
from apps.users.permissions import IsAdminUser
from apps.audits.models import AuditLog
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['7. Reportes'])
class ReportViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    """
    API de Reportes y Moderación.
    - Usuarios: Crean reportes y ven los suyos.
    - Admins: Gestionan reportes, banean vendedores o desestiman quejas.
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated] 

    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
        user = self.request.user
        
        # Admin ve todo (con filtros)
        if user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'admin':
            status_param = self.request.query_params.get('status', None)
            if status_param:
                return Report.objects.filter(status=status_param)
            return Report.objects.all()
        
        # Usuarios normales no ven la lista general
        return Report.objects.none() 

    def get_permissions(self):
        """ Configuración de permisos por acción """
        if self.action in ['create', 'my_reports']:
            return [permissions.IsAuthenticated()] 
        
        # Para moderar (banear, desestimar, listar), solo Admin
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'ban_vendor', 'dismiss_report']:
            return [IsAdminUser()]
            
        return [permissions.IsAuthenticated()]
    
    # --- ENDPOINT: MIS REPORTES (Usuario) ---
    @extend_schema(summary="Mis Reportes")
    @action(detail=False, methods=['get'])
    def my_reports(self, request):
        user_reports = Report.objects.filter(reporter=self.request.user.profile)
        page = self.paginate_queryset(user_reports)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(user_reports, many=True)
        return Response(serializer.data)

    # =========================================================
    #  MODERACIÓN 1: BANEAR AL VENDEDOR (Reporte Válido)
    # =========================================================
    @extend_schema(summary="Aceptar Reporte y Banear Vendedor")
    @action(detail=True, methods=['post'], url_path='ban-vendor')
    def ban_vendor(self, request, pk=None):
        """
        1. Banea al dueño del producto reportado.
        2. Copia el MOTIVO del reporte al perfil del usuario (sin fotos).
        3. Marca el reporte como Resuelto.
        """
        try:
            report = self.get_object()
        except Report.DoesNotExist:
            return Response({'error': 'Reporte no encontrado'}, status=404)

        # Obtenemos al dueño del producto
        vendor_profile = report.product.vendor
        
        if not vendor_profile:
            return Response({'error': 'El producto no tiene vendedor asociado.'}, status=400)

        # 1. Aplicar Baneo
        vendor_profile.is_banned = True
        
        # 2. Copiar Motivo (Texto puro, SIN la foto de evidencia)
        vendor_profile.ban_reason = f"Reporte en producto '{report.product.name}': {report.reason}"
        vendor_profile.save()

        # 3. Actualizar Reporte
        report.status = 'resolved'
        report.save()

        # Auditoría
        AuditLog.objects.create(
            user=request.user,
            action='USER_BANNED',
            details=f"Admin baneó a {vendor_profile.user.username} por reporte #{report.id}"
        )

        return Response({
            "status": "success", 
            "message": f"Usuario {vendor_profile.user.username} baneado correctamente. Motivo registrado."
        })

    # =========================================================
    #  MODERACIÓN 2: DESESTIMAR REPORTE (Evidencia Insuficiente)
    # =========================================================
    @extend_schema(summary="Desestimar Reporte (Evidencia Insuficiente)")
    @action(detail=True, methods=['post'], url_path='dismiss')
    def dismiss_report(self, request, pk=None):
        """
        Marca el reporte como resuelto SIN tomar acción contra el vendedor.
        Se usa cuando las pruebas no son suficientes.
        """
        try:
            report = self.get_object()
        except Report.DoesNotExist:
            return Response({'error': 'Reporte no encontrado'}, status=404)

        # Solo cambiamos el estatus a resuelto (se cierra el caso)
        report.status = 'resolved'
        report.save()

        AuditLog.objects.create(
            user=request.user,
            action='REPORT_DISMISSED',
            details=f"Reporte #{report.id} desestimado por falta de pruebas."
        )

        return Response({
            "status": "success", 
            "message": "Reporte cerrado sin penalización (Evidencia insuficiente)."
        })
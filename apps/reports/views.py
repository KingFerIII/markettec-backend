# En: apps/reports/views.py

from rest_framework import viewsets, mixins, permissions, status, response # <-- ¡AÑADIDO permissions!
from rest_framework.decorators import action # <-- ¡AÑADIDO action!
from rest_framework.response import Response # <-- ¡AÑADIDO Response!
from .models import Report
from .serializers import ReportSerializer
from .permissions import IsAdminOrReadOnly
from apps.users.permissions import IsAdminUser
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['7. Reportes'])
class ReportViewSet(mixins.CreateModelMixin,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   viewsets.GenericViewSet):
    """
    Endpoint de API para Reportes.
    - Usuarios (POST): Pueden CREAR reportes.
    - Usuarios (GET /my_reports/): Pueden VER SUS reportes.
    - Admins (GET, PATCH): Pueden VER TODOS y ACTUALIZAR reportes.
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAdminOrReadOnly] 

    def get_serializer_context(self):
        """ Pasa el 'request' al serializer. """
        return {'request': self.request}

    def get_queryset(self):
        """
        Esta función filtra la lista principal (GET /api/reports/).
        Los Admins ven los reportes pendientes (por defecto).
        Los no-admins ven una lista vacía (controlado por el permiso).
        """
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'admin':
            status = self.request.query_params.get('status', 'pending')
            return Report.objects.filter(status=status)
        
        return Report.objects.none() 

    def get_permissions(self):
        """ Asigna permisos basados en la acción. """

        # --- ¡NUEVA REGLA AÑADIDA! ---
        if self.action == 'my_reports':
            # Solo requiere estar logueado
            return [permissions.IsAuthenticated()] 
        # --------------------------------

        if self.action in ['update', 'partial_update']:
            # Solo Admins pueden cambiar el 'status'
            return [IsAdminUser()]
            
        return super().get_permissions()
    
    def update(self, request, *args, **kwargs):
        """
        Sobrescribimos el método 'update' (que maneja PATCH)
        para permitir a los Admins cambiar el 'status' 
        (incluso si es 'read_only' en el serializer).
        """
        # (El permiso 'IsAdminUser' ya protegió esta acción)
        instance = self.get_object() # Obtiene el reporte
        new_status = request.data.get('status') # Obtiene el "resolved" del frontend

        if new_status not in ['pending', 'resolved']:
            return response.Response(
                {'error': 'Ese no es un estado válido.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizamos el estado manualmente
        instance.status = new_status
        instance.save()
        
        # Devolvemos la instancia actualizada
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)
    # --- FIN DEL MÉTODO NUEVO ---

    # --- ¡NUEVO ENDPOINT AÑADIDO AL FINAL! ---
    @extend_schema(summary="Mis Reportes")
    @action(detail=False, methods=['get'])
    def my_reports(self, request):
        """
        Endpoint para ver solo los reportes creados
        por el usuario actualmente logueado.
        URL: GET /api/reports/my_reports/
        """
        # (El permiso 'IsAuthenticated' ya protegió esto)
        
        # Filtramos los reportes donde el 'reporter' sea el perfil del usuario
        user_reports = Report.objects.filter(reporter=self.request.user.profile)
        
        # Paginamos los resultados (buena práctica)
        page = self.paginate_queryset(user_reports)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # Serializamos y devolvemos
        serializer = self.get_serializer(user_reports, many=True)
        return Response(serializer.data)
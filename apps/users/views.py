# En: apps/users/views.py

from rest_framework import viewsets, permissions, decorators, response, status, mixins
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, RegisterSerializer
from .permissions import IsAdminUser, IsOwnerOrAdmin
from apps.audits.models import AuditLog

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    Endpoint para ver y gestionar usuarios.
    Altamente restringido por la función 'get_permissions'.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """
        Asigna permisos específicos basados en la acción (list, create, retrieve, etc.)
        """
        permission_classes = []
        
        # --- ¡PERMISOS ACTUALIZADOS! ---
        if self.action in [
            'list', 'create', 'destroy', 
            'banned_users', 'ban_user', 'unban_user' # Nuevas acciones de admin
        ]:
            # Solo Admins pueden listar, crear, borrar o banear.
            permission_classes = [IsAdminUser]
            
        elif self.action in ['retrieve', 'update', 'partial_update']:
            # El dueño o un Admin pueden ver/editar un perfil específico por ID.
            permission_classes = [IsOwnerOrAdmin]
            
        elif self.action == 'profile':
            # Tu endpoint personalizado: cualquier usuario autenticado puede ver SU perfil.
            permission_classes = [permissions.IsAuthenticated]
            
        else:
            # Cualquier otra acción futura, por seguridad, solo admin.
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]

    @decorators.action(detail=False, methods=['get'])
    def profile(self, request):
        """
        Devuelve los datos del usuario autenticado.
        Endpoint: GET /api/users/profile/
        """
        serializer = self.get_serializer(request.user)
        return response.Response(serializer.data)

    # --- ¡NUEVA ACCIÓN PARA VER BANEADOS! ---
    @decorators.action(detail=False, methods=['get'])
    def banned_users(self, request):
        """
        Endpoint solo para Admins.
        Devuelve una lista de usuarios con 'is_banned=True'.
        URL: GET /api/users/banned_users/
        """
        # (El permiso 'IsAdminUser' ya protegió esta acción)
        
        # Filtramos usuarios cuyo perfil tenga is_banned = True
        banned_users = User.objects.filter(profile__is_banned=True)
        
        # Paginamos (si está configurado)
        page = self.paginate_queryset(banned_users)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(banned_users, many=True)
        return response.Response(serializer.data)

    # --- ¡NUEVA ACCIÓN PARA BANEAR! ---
    @decorators.action(detail=True, methods=['post'])
    def ban_user(self, request, pk=None):
        """
        Endpoint solo para Admins. Marca a un usuario como baneado.
        URL: POST /api/users/<id>/ban_user/
        """
        try:
            user = self.get_object() # Obtiene el usuario
        except User.DoesNotExist:
            return response.Response(
                {'error': 'Usuario no encontrado.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        reason = request.data.get('reason')
        if not reason:
            return response.Response(
                {'error': 'Se requiere una razón (reason) para banear.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if hasattr(user, 'profile'): # Comprobamos que tenga perfil
            user.profile.is_banned = True
            user.profile.ban_reason = reason
            user.profile.save()
            
            # Registrar en la bitácora
            AuditLog.objects.create(
                user=request.user, # El admin que hace la acción
                action='USER_BANNED',
                details=f"Admin '{request.user.username}' baneó a '{user.username}' (ID: {user.id})"
            )
            
            return response.Response(
                {'status': f'Usuario {user.username} ha sido baneado.'},
                status=status.HTTP_200_OK
            )
        return response.Response(
            {'error': 'El usuario no tiene perfil.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    # --- ¡NUEVA ACCIÓN PARA DESBANEAR! ---
    @decorators.action(detail=True, methods=['post'])
    def unban_user(self, request, pk=None):
        """
        Endpoint solo para Admins. Quita el baneo a un usuario.
        URL: POST /api/users/<id>/unban_user/
        """
        try:
            user = self.get_object() # Obtiene el usuario
        except User.DoesNotExist:
            return response.Response(
                {'error': 'Usuario no encontrado.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        if hasattr(user, 'profile'): # Comprobamos que tenga perfil
            user.profile.is_banned = False
            user.profile.ban_reason = None
            user.profile.save()
            
            # Registrar en la bitácora
            AuditLog.objects.create(
                user=request.user, # El admin que hace la acción
                action='USER_UNBANNED',
                details=f"Admin '{request.user.username}' quitó el baneo a '{user.username}' (ID: {user.id})"
            )
            
            return response.Response(
                {'status': f'Usuario {user.username} ha sido desbaneado.'},
                status=status.HTTP_200_OK
            )
        return response.Response(
            {'error': 'El usuario no tiene perfil.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Endpoint para registrar un nuevo usuario (solo acción 'create').
    """
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        """
        Registra un nuevo usuario, crea un log de auditoría
        y devuelve sus tokens JWT.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 1. El usuario se guarda en la base de datos
        user = serializer.save() 

        # --- ¡CONEXIÓN DE BITÁCORA! ---
        # 2. Creamos el registro de auditoría
        AuditLog.objects.create(
            user=user, # Asocia el log al usuario que se acaba de crear
            action='USER_REGISTERED',
            details=f"Nuevo usuario registrado: '{user.username}' (ID: {user.id})"
        )
        # --- FIN DE BITÁCORA ---

        # 3. Generar tokens JWT automáticamente
        refresh = RefreshToken.for_user(user)

        # 4. Devolver la respuesta
        return response.Response({
            "user": serializer.data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
from rest_framework import viewsets, permissions, decorators, response, status, mixins
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, RegisterSerializer
from .permissions import IsAdminUser, IsOwnerOrAdmin
from apps.audits.models import AuditLog
from drf_spectacular.utils import extend_schema

User = get_user_model()

@extend_schema(tags=['2. Usuarios'])
class UserViewSet(viewsets.ModelViewSet):
    """
    Endpoint para ver y gestionar usuarios.
    Permite a los Admins ver la lista completa y banear, 
    y a los usuarios editar su propio perfil.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'profile':
            from .serializers import SimpleUserSerializer
            return SimpleUserSerializer
        return UserSerializer

    def get_permissions(self):
        permission_classes = []
        
        # 'create' aquí se refiere a un Admin creando usuarios manualmente (/api/users/)
        if self.action in ['list', 'create', 'destroy', 'banned_users', 'ban_user', 'unban_user']:
            permission_classes = [IsAdminUser]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            permission_classes = [IsOwnerOrAdmin]
        elif self.action == 'profile':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]

    @extend_schema(tags=['2. Usuarios'], summary="Ver Perfil (Usuario Logueado)")
    @decorators.action(detail=False, methods=['get'])
    def profile(self, request):
        """ Devuelve los datos del usuario autenticado (sin campos sensibles). """
        serializer = self.get_serializer(request.user)
        return response.Response(serializer.data)

    @extend_schema(tags=['2. Usuarios'], summary="Ver Lista de Baneados (Admin)")
    @decorators.action(detail=False, methods=['get'])
    def banned_users(self, request):
        """ Devuelve una lista de usuarios con 'is_banned=True'. """
        banned_users = User.objects.filter(profile__is_banned=True)
        page = self.paginate_queryset(banned_users)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(banned_users, many=True)
        return response.Response(serializer.data)

    @extend_schema(tags=['2. Usuarios'], summary="Banear Usuario (Admin)")
    @decorators.action(detail=True, methods=['post'])
    def ban_user(self, request, pk=None):
        try:
            user = self.get_object() 
        except User.DoesNotExist:
            return response.Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        reason = request.data.get('reason')
        if not reason:
            return response.Response({'error': 'Se requiere una razón (reason) para banear.'}, status=status.HTTP_400_BAD_REQUEST)
        if hasattr(user, 'profile'): 
            user.profile.is_banned = True
            user.profile.ban_reason = reason
            user.profile.save()
            AuditLog.objects.create(
                user=request.user, action='USER_BANNED', details=f"Admin '{request.user.username}' baneó a '{user.username}'. Razón: {reason}"
            )
            return response.Response({'status': f'Usuario {user.username} ha sido baneado.'}, status=status.HTTP_200_OK)
        return response.Response({'error': 'El usuario no tiene perfil.'}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(tags=['2. Usuarios'], summary="Desbanear Usuario (Admin)")
    @decorators.action(detail=True, methods=['post'])
    def unban_user(self, request, pk=None):
        try:
            user = self.get_object() 
        except User.DoesNotExist:
            return response.Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(user, 'profile'):
            user.profile.is_banned = False
            user.profile.ban_reason = None
            user.profile.save()
            AuditLog.objects.create(
                user=request.user, action='USER_UNBANNED', details=f"Admin '{request.user.username}' quitó el baneo a '{user.username}'"
            )
            return response.Response({'status': f'Usuario {user.username} ha sido desbaneado.'}, status=status.HTTP_200_OK)
        return response.Response({'error': 'El usuario no tiene perfil.'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['1. Autenticación'], summary="Registro de Usuario")
class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Endpoint para registrar un nuevo usuario (solo acción 'create').
    """
    queryset = User.objects.all()
    
    # --- ¡LA SOLUCIÓN! ---
    # Desactivamos la autenticación para este endpoint. 
    # Así, si Android manda un token viejo por error, NO fallará.
    authentication_classes = [] 
    permission_classes = [permissions.AllowAny]
    # ---------------------
    
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        """ Registra un nuevo usuario y devuelve sus tokens JWT. """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save() 
        
        # AuditLog puede fallar si 'user' no está autenticado (request.user es Anonymous),
        # pero aquí 'user' es el nuevo usuario creado.
        AuditLog.objects.create(user=user, action='USER_REGISTERED', details=f"Nuevo usuario registrado: '{user.username}' (ID: {user.id})")
        
        refresh = RefreshToken.for_user(user)
        return response.Response({
            "user": serializer.data, "refresh": str(refresh), "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
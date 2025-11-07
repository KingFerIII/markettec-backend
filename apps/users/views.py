# En: apps/users/views.py

from rest_framework import viewsets, permissions, decorators, response, status, mixins
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

# --- Importamos los serializers y permisos correctos ---
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
    serializer_class = UserSerializer # <-- Usa el UserSerializer (con Perfil)

    def get_permissions(self):
        """
        Asigna permisos específicos basados en la acción (list, create, retrieve, etc.)
        """
        permission_classes = []
        
        if self.action in ['list', 'create', 'destroy']:
            # Solo Admins pueden listar, crear (desde aquí) o borrar usuarios.
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
        (Este método está perfecto como lo tenías)
        """
        serializer = self.get_serializer(request.user)
        return response.Response(serializer.data)


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
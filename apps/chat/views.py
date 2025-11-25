from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from apps.users.models import Profile
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

@extend_schema(tags=['9. Chat'])
class ConversationViewSet(viewsets.ModelViewSet):
    """
    API de Chats.
    - GET /api/chat/ -> Lista tus conversaciones.
    - DELETE /api/chat/{id}/ -> Borra una conversación completa.
    - POST /api/chat/start_chat/ -> Inicia/Obtiene un chat con un usuario.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """ Solo muestra conversaciones donde YO soy parte """
        profile = self.request.user.profile
        return Conversation.objects.filter(Q(user_a=profile) | Q(user_b=profile))

    @extend_schema(
        summary="Iniciar Chat",
        request=None,
        parameters=[
            OpenApiParameter(name='target_user_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY)
        ]
    )
    @action(detail=False, methods=['post'])
    def start_chat(self, request):
        """
        Crea o recupera un chat con otro usuario.
        Uso: POST /api/chat/start_chat/?target_user_id=5
        """
        target_user_id = request.query_params.get('target_user_id')
        my_profile = request.user.profile
        
        # Validación
        target_profile = get_object_or_404(Profile, user_id=target_user_id)
        
        if my_profile == target_profile:
            return Response({"error": "No puedes chatear contigo mismo"}, status=400)

        # Buscamos si ya existe (A-B o B-A)
        chat = Conversation.objects.filter(
            (Q(user_a=my_profile) & Q(user_b=target_profile)) |
            (Q(user_a=target_profile) & Q(user_b=my_profile))
        ).first()

        if not chat:
            # Si no existe, creamos uno nuevo
            chat = Conversation.objects.create(user_a=my_profile, user_b=target_profile)

        serializer = self.get_serializer(chat)
        return Response(serializer.data)


@extend_schema(tags=['9. Chat'])
class MessageViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """
    API de Mensajes.
    - GET /api/messages/?conversation_id=1 -> Ver mensajes de un chat.
    - POST /api/messages/ -> Enviar mensaje (Texto, Foto, Audio o Ubicación).
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """ Filtra mensajes por ID de conversación """
        conversation_id = self.request.query_params.get('conversation_id')
        if not conversation_id:
            return Message.objects.none()
        
        # Seguridad: Solo ver mensajes si soy parte del chat
        return Message.objects.filter(conversation_id=conversation_id)

    def perform_create(self, serializer):
        """ Al guardar, asignamos el remitente y actualizamos la fecha del chat """
        conversation = serializer.validated_data['conversation']
        me = self.request.user.profile
        
        # Validar que pertenezco al chat
        if conversation.user_a != me and conversation.user_b != me:
            raise permissions.PermissionDenied("No perteneces a este chat")
            
        serializer.save(sender=me)
        
        # Actualizar fecha de la conversación (para que suba en la lista)
        conversation.save()
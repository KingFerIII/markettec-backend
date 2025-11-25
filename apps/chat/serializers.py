from rest_framework import serializers
from .models import Conversation, Message
from apps.users.serializers import PublicProfileSerializer
from django.db.models import Q

class MessageSerializer(serializers.ModelSerializer):
    """ Serializer para enviar/recibir mensajes """
    sender_data = PublicProfileSerializer(source='sender', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'sender_data', 
            'text', 'image', 'audio', 'location', 
            'created_at', 'is_read'
        ]
        read_only_fields = ('sender', 'is_read')

class ConversationSerializer(serializers.ModelSerializer):
    """ Serializer para la lista de chats """
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'user_a', 'user_b', 'other_user', 'last_message', 'updated_at']

    def get_other_user(self, obj):
        """ Devuelve la info del OTRO usuario (con el que estás hablando) """
        request = self.context.get('request')
        if not request: return None
        
        me = request.user.profile
        other = obj.user_b if obj.user_a == me else obj.user_a
        return PublicProfileSerializer(other).data

    def get_last_message(self, obj):
        """ Muestra el último mensaje para la vista previa """
        last_msg = obj.messages.last()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
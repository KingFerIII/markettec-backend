from django.db import models
from apps.users.models import Profile

class Conversation(models.Model):
    """
    Representa la 'Sala de Chat' entre dos usuarios.
    """
    user_a = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='conversations_as_a')
    user_b = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='conversations_as_b')
    
    updated_at = models.DateTimeField(auto_now=True) # Para ordenar por el chat más reciente

    class Meta:
        # Evitamos duplicados: Solo puede haber una conversación entre A y B
        unique_together = ('user_a', 'user_b')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat: {self.user_a} <-> {self.user_b}"

class Message(models.Model):
    """
    Cada mensaje individual dentro de la conversación.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE)
    
    # --- CONTENIDO ---
    text = models.TextField(blank=True, null=True) # Texto normal
    
    # --- MULTIMEDIA (Lo que pidió Javi) ---
    image = models.ImageField(upload_to='chat/images/', blank=True, null=True)
    audio = models.FileField(upload_to='chat/audio/', blank=True, null=True)
    
    # Ubicación: Guardaremos "latitud,longitud" como texto (ej. "19.432,-99.133")
    location = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at'] # Orden cronológico (antiguos primero)

    def __str__(self):
        return f"Msg de {self.sender} en Chat {self.conversation.id}"
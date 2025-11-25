from django.contrib import admin
from .models import Conversation, Message

# Esto permite ver los mensajes DENTRO de la pantalla de la Conversación
class MessageInline(admin.TabularInline):
    model = Message
    extra = 0 # No muestra filas vacías extra
    readonly_fields = ('sender', 'text', 'image', 'audio', 'location', 'created_at')
    can_delete = True

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_a', 'user_b', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('user_a__user__username', 'user_b__user__username')
    inlines = [MessageInline] # ¡Aquí activamos la vista de mensajes dentro del chat!

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'conversation', 'created_at', 'has_image', 'has_audio', 'is_read')
    list_filter = ('created_at', 'is_read')
    search_fields = ('text', 'sender__user__username')

    # Helpers para mostrar íconos en la lista si tiene foto/audio
    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Tiene Foto'

    def has_audio(self, obj):
        return bool(obj.audio)
    has_audio.boolean = True
    has_audio.short_description = 'Tiene Audio'
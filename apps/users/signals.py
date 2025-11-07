# En: apps/users/signals.py

from django.dispatch import receiver
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created
from django.core.mail import send_mail  


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Este "oyente" se activa cuando se crea un token de reseteo.
    Se encarga de enviar el correo al usuario.
    """
    
    # El token que el usuario usará
    token = reset_password_token.key
    
    # El correo del usuario
    email_to = reset_password_token.user.email
    
    # El asunto del correo
    subject = "Restablecimiento de Contraseña para MarketTec"

    # El cuerpo del mensaje (¡AQUÍ VA EL TOKEN!)
    message = f"""
    Hola,

    Hemos recibido una solicitud para restablecer tu contraseña.

    Usa el siguiente token para confirmar tu nueva contraseña:
    
    {token}

    Si no solicitaste esto, por favor ignora este correo.

    Gracias,
    El equipo de MarketTec
    """

    # Enviar el correo
    send_mail(
        subject,
        message,
        "no-reply@markettec.com", # Email remitente (puede ser cualquiera)
        [email_to], # Email destinatario
        fail_silently=False,
    )
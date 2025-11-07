from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'

    # --- ¡CORREGIDO! ---
    # (Añade una tabulación aquí)
    def ready(self): 
        # Importa los signals cuando la app esté lista
        import apps.users.signals
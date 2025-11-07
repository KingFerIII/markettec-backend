# En: apps/users/admin.py

from django.contrib import admin
from .models import Profile # <-- Importa tu modelo Profile

# Registra SOLO el modelo Profile
admin.site.register(Profile)

# ¡No registres el 'User' aquí! Django ya lo hace.
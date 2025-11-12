# En: apps/favorites/urls.py

from rest_framework.routers import DefaultRouter
from .views import FavoriteViewSet

# Creamos un router, igual que en las otras apps
router = DefaultRouter()

# Registramos nuestro ViewSet.
# Esto crea automáticamente:
# GET /api/favorites/ (para listar)
# POST /api/favorites/ (para crear)
# DELETE /api/favorites/<id>/ (para borrar)
router.register(r'favorites', FavoriteViewSet, basename='favorite')

# Exportamos las URLs generadas por el router
urlpatterns = router.urls
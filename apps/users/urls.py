from rest_framework.routers import DefaultRouter
from .views import UserViewSet, RegisterViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'register', RegisterViewSet, basename='register')

urlpatterns = router.urls

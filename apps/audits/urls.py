# En: apps/audits/urls.py
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet

router = DefaultRouter()
router.register(r'audits', AuditLogViewSet, basename='auditlog')

urlpatterns = router.urls
from rest_framework.routers import DefaultRouter
from .views import ManufacturerViewSet

router = DefaultRouter()
router.register(r'manufacturers', ManufacturerViewSet, basename='manufacturer')

urlpatterns = router.urls
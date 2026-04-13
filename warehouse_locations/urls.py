from rest_framework.routers import DefaultRouter
from .views import WarehouseRackViewSet, WarehouseCellViewSet

router = DefaultRouter()
router.register(r'racks', WarehouseRackViewSet, basename='rack')
router.register(r'cells', WarehouseCellViewSet, basename='cell')

urlpatterns = router.urls
from rest_framework.routers import DefaultRouter
from .views import WarehouseItemViewSet, WarehouseTransactionViewSet

router = DefaultRouter()
router.register(r'warehouse', WarehouseItemViewSet, basename='warehouse')
router.register(r'transactions', WarehouseTransactionViewSet, basename='transaction')

urlpatterns = router.urls
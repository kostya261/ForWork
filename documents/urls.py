from rest_framework.routers import DefaultRouter
from .views import MaterialRequestViewSet, InventoryIssueViewSet

router = DefaultRouter()
router.register(r'material-requests', MaterialRequestViewSet, basename='material-request')
router.register(r'inventory-issues', InventoryIssueViewSet, basename='inventory-issue')

urlpatterns = router.urls
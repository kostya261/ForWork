from rest_framework.routers import DefaultRouter
from .views import UserViewSet, PositionViewSet, DepartmentViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'positions', PositionViewSet, basename='position')
router.register(r'departments', DepartmentViewSet, basename='department')

urlpatterns = router.urls
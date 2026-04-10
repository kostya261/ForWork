from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, MessageViewSet, UserChatStatusViewSet

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='room')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'status', UserChatStatusViewSet, basename='status')

urlpatterns = router.urls
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import ChatRoom, Message, UserChatStatus
from .serializers import (
    ChatRoomListSerializer, ChatRoomDetailSerializer,
    MessageSerializer, CreatePrivateChatSerializer,
    UserChatStatusSerializer
)


class ChatRoomViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'participants__username']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        """Показываем только комнаты, в которых участвует пользователь"""
        user = self.request.user
        return ChatRoom.objects.filter(participants=user).distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatRoomListSerializer
        if self.action == 'create_private':
            return CreatePrivateChatSerializer
        return ChatRoomDetailSerializer

    def perform_create(self, serializer):
        """При создании комнаты добавляем создателя в участники"""
        chat = serializer.save(created_by=self.request.user)
        chat.participants.add(self.request.user)

    @action(detail=False, methods=['post'])
    def create_private(self, request):
        """Создать или получить личный чат с пользователем"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chat = serializer.save()

        return Response(
            ChatRoomDetailSerializer(chat, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def public(self, request):
        """Получить общий чат (или создать, если нет)"""
        public_chat = ChatRoom.objects.filter(room_type='public').first()

        if not public_chat:
            public_chat = ChatRoom.objects.create(
                name='Общий чат',
                room_type='public',
                created_by=request.user
            )
            # Добавляем всех активных пользователей
            from django.contrib.auth import get_user_model
            User = get_user_model()
            public_chat.participants.add(*User.objects.filter(is_active=True))

        # Добавляем текущего пользователя, если его там нет
        if request.user not in public_chat.participants.all():
            public_chat.participants.add(request.user)

        serializer = ChatRoomDetailSerializer(public_chat, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Отправить сообщение в комнату"""
        room = self.get_object()

        # Проверяем, что пользователь в комнате
        if request.user not in room.participants.all():
            return Response(
                {'error': 'Вы не участвуете в этом чате'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MessageSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(room=room)

        # Обновляем время комнаты
        room.save()  # auto_now сработает

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Отметить все сообщения в комнате как прочитанные"""
        room = self.get_object()

        unread_messages = room.messages.filter(
            is_read=False
        ).exclude(sender=request.user)

        count = unread_messages.count()
        unread_messages.update(is_read=True)

        return Response({'marked_read': count})

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Получить сообщения комнаты с пагинацией"""
        room = self.get_object()

        # Параметры пагинации
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))

        messages = room.messages.all()[offset:offset + limit]
        serializer = MessageSerializer(messages, many=True, context={'request': request})

        return Response({
            'count': room.messages.count(),
            'results': serializer.data
        })


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().select_related('sender', 'room').prefetch_related('attachments')
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['text']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Показываем только сообщения из комнат, где участвует пользователь"""
        user = self.request.user
        return super().get_queryset().filter(room__participants=user)


class UserChatStatusViewSet(viewsets.ModelViewSet):
    queryset = UserChatStatus.objects.all().select_related('user')
    serializer_class = UserChatStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    filterset_fields = ['is_online']

    @action(detail=False, methods=['post'])
    def set_online(self, request):
        """Установить статус онлайн"""
        status_obj, created = UserChatStatus.objects.get_or_create(user=request.user)
        status_obj.is_online = True
        status_obj.save()
        return Response(UserChatStatusSerializer(status_obj).data)

    @action(detail=False, methods=['post'])
    def set_offline(self, request):
        """Установить статус офлайн"""
        status_obj, created = UserChatStatus.objects.get_or_create(user=request.user)
        status_obj.is_online = False
        status_obj.save()
        return Response(UserChatStatusSerializer(status_obj).data)

    @action(detail=False, methods=['get'])
    def online_users(self, request):
        """Список пользователей онлайн"""
        online_statuses = self.get_queryset().filter(is_online=True)
        return Response(UserChatStatusSerializer(online_statuses, many=True).data)
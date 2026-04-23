from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, UserChatStatus

User = get_user_model()


class UserChatStatusSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = UserChatStatus
        fields = ['user', 'user_name', 'is_online', 'last_activity']


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    attachments_urls = serializers.SerializerMethodField()
    room_name = serializers.CharField(source='room.name', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'room', 'room_name',
            'sender', 'sender_name',
            'text', 'attachments', 'attachments_urls',
            'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['sender', 'is_read', 'read_at', 'created_at']

    def get_attachments_urls(self, obj):
        request = self.context.get('request')
        urls = []
        for img in obj.attachments.all():
            if img.image and request:
                urls.append(request.build_absolute_uri(img.image.url))
        return urls

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['sender'] = request.user
        return super().create(validated_data)


class ChatRoomListSerializer(serializers.ModelSerializer):
    """Список комнат с последним сообщением"""
    room_type_display = serializers.CharField(source='get_room_type_display', read_only=True)
    participants_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'name', 'room_type', 'room_type_display',
            'participants_count', 'other_participant',
            'last_message', 'unread_count',
            'created_at', 'updated_at'
        ]

    def get_participants_count(self, obj):
        return obj.participants.count()

    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return MessageSerializer(last_msg, context=self.context).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        user = request.user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

    def get_other_participant(self, obj):
        """Для личных чатов показываем собеседника"""
        request = self.context.get('request')
        user = request.user

        if obj.room_type == 'private':
            other = obj.participants.exclude(id=user.id).first()
            if other:
                return {
                    'id': other.id,
                    'username': other.username,
                    'full_name': other.get_full_name()
                }
        return None


class ChatRoomDetailSerializer(serializers.ModelSerializer):
    """Детальная информация о комнате с сообщениями"""
    participants = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()
    room_type_display = serializers.CharField(source='get_room_type_display', read_only=True)

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'name', 'room_type', 'room_type_display',
            'participants', 'messages',
            'created_at', 'updated_at'
        ]

    def get_participants(self, obj):
        participants = obj.participants.all()
        return [
            {
                'id': p.id,
                'username': p.username,
                'full_name': p.get_full_name(),
                'is_online': hasattr(p, 'chat_status') and p.chat_status.is_online
            }
            for p in participants
        ]

    def get_messages(self, obj):
        # По умолчанию отдаем последние 50 сообщений
        messages = obj.messages.all()[:50]
        return MessageSerializer(messages, many=True, context=self.context).data


class CreatePrivateChatSerializer(serializers.Serializer):
    """Создание личного чата с пользователем"""
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('Пользователь не найден')
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        other_user = User.objects.get(id=validated_data['user_id'])
        current_user = request.user

        # Проверяем, существует ли уже чат между этими пользователями
        existing_chat = ChatRoom.objects.filter(
            room_type='private',
            participants=current_user
        ).filter(
            participants=other_user
        ).first()

        if existing_chat:
            return existing_chat

        # Создаем новый чат
        chat = ChatRoom.objects.create(
            room_type='private',
            created_by=current_user
        )
        chat.participants.add(current_user, other_user)

        return chat
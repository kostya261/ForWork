from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatRoom(models.Model):
    """
    Комната чата (общая или личная).
    """
    ROOM_TYPES = (
        ('public', 'Общий чат'),
        ('private', 'Личная переписка'),
    )

    name = models.CharField(max_length=100, blank=True, verbose_name='Название комнаты')
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='private', verbose_name='Тип комнаты')

    participants = models.ManyToManyField(
        User,
        related_name='chat_rooms',
        verbose_name='Участники'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_chat_rooms',
        verbose_name='Создатель'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Чат-комната'
        verbose_name_plural = 'Чат-комнаты'
        ordering = ['-updated_at']

    def __str__(self):
        if self.room_type == 'public':
            return self.name or 'Общий чат'
        else:
            participants_list = list(self.participants.values_list('username', flat=True))
            return f"Чат: {' и '.join(participants_list)}"

    def save(self, *args, **kwargs):
        """Автоматически генерируем имя для общего чата"""
        is_new = not self.pk
        super().save(*args, **kwargs)

        if is_new and self.room_type == 'public' and not self.name:
            self.name = f'Общий чат #{self.pk}'
            self.save(update_fields=['name'])


class Message(models.Model):
    """
    Сообщение в чате.
    """
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Комната'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='chat_messages',
        verbose_name='Отправитель'
    )

    text = models.TextField(blank=True, verbose_name='Текст сообщения')

    # Вложения (из галереи)
    attachments = models.ManyToManyField(
        'gallery.Image',
        blank=True,
        related_name='chat_messages',
        verbose_name='Вложения'
    )

    # Статус прочтения (для личных сообщений)
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата прочтения')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.text[:50]}..." if self.text else f"{self.sender}: [Вложение]"

    def mark_as_read(self):
        """Отметить сообщение как прочитанное"""
        if not self.is_read:
            self.is_read = True
            self.read_at = models.DateTimeField(auto_now=True)
            self.save(update_fields=['is_read', 'read_at'])


class UserChatStatus(models.Model):
    """
    Статус пользователя в чате (онлайн/офлайн, последняя активность).
    Пригодится для WebSockets.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='chat_status',
        verbose_name='Пользователь'
    )
    is_online = models.BooleanField(default=False, verbose_name='Онлайн')
    last_activity = models.DateTimeField(auto_now=True, verbose_name='Последняя активность')

    class Meta:
        verbose_name = 'Статус в чате'
        verbose_name_plural = 'Статусы в чате'

    def __str__(self):
        status = '🟢' if self.is_online else '🔴'
        return f"{self.user.username} {status}"
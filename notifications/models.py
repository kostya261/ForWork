from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    TYPE_CHOICES = (
        ('task_assigned', 'Назначена задача'),
        ('task_status', 'Изменён статус задачи'),
        ('task_comment', 'Новый комментарий'),
        ('chat_message', 'Новое сообщение'),
        ('document_created', 'Создан документ'),
        ('system', 'Системное'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)  # URL для перехода
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
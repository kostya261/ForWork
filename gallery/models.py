from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Image(models.Model):
    """
    Универсальная модель для хранения изображений.
    Можно прикреплять к любой другой модели через ForeignKey.
    """
    title = models.CharField(max_length=100, blank=True, verbose_name='Название')
    image = models.ImageField(upload_to='gallery/%Y/%m/', verbose_name='Изображение')
    description = models.TextField(blank=True, verbose_name='Описание')

    # Кто загрузил
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_images',
        verbose_name='Загрузил'
    )

    # Когда загружено
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'
        ordering = ['-created_at']

    def __str__(self):
        return self.title or f"Изображение #{self.pk}"
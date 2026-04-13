import hashlib

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

    # Хеш для проверки дубликатов
    file_hash = models.CharField(max_length=64, blank=True, verbose_name='Хеш файла')

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

    def save(self, *args, **kwargs):
        # Вычисляем хеш при первой загрузке
        if self.image and not self.file_hash:
            self.image.seek(0)
            hasher = hashlib.sha256()
            for chunk in self.image.chunks():
                hasher.update(chunk)
            self.file_hash = hasher.hexdigest()

        # Проверяем, нет ли уже изображения с таким хешем
        if self.file_hash:
            existing = Image.objects.filter(file_hash=self.file_hash).first()
            if existing and existing.pk != self.pk:
                # Файл уже существует — не сохраняем дубликат
                # Но нам нужно вернуть существующий объект
                # Поэтому просто присваиваем self.pk = existing.pk
                # Это сложно в save(), лучше обрабатывать во view
                pass

        super().save(*args, **kwargs)
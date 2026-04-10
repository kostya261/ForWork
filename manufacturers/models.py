from django.db import models


class Manufacturer(models.Model):
    """
    Производитель оборудования / расходников.
    """
    name = models.CharField(max_length=200, unique=True, verbose_name='Наименование')
    description = models.TextField(blank=True, verbose_name='Описание')
    logo = models.ForeignKey(
        'gallery.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Логотип'
    )
    website = models.URLField(blank=True, verbose_name='Сайт')
    country = models.CharField(max_length=100, blank=True, verbose_name='Страна')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'
        ordering = ['name']

    def __str__(self):
        return self.name
from django.db import models


class Bank(models.Model):
    """
    Банковские реквизиты и информация о банке как о юрлице.
    """
    # Основная информация
    name = models.CharField(max_length=200, verbose_name='Наименование банка')
    short_name = models.CharField(max_length=100, blank=True, verbose_name='Краткое наименование')
    description = models.TextField(blank=True, verbose_name='Описание')

    # Реквизиты банка как юрлица
    inn = models.CharField(max_length=12, blank=True, verbose_name='ИНН банка')
    kpp = models.CharField(max_length=9, blank=True, verbose_name='КПП банка')
    ogrn = models.CharField(max_length=15, blank=True, verbose_name='ОГРН банка')

    # Адрес
    legal_address = models.TextField(blank=True, verbose_name='Юридический адрес')
    actual_address = models.TextField(blank=True, verbose_name='Фактический адрес')

    # Банковские идентификаторы
    bik = models.CharField(max_length=9, unique=True, verbose_name='БИК')
    swift = models.CharField(max_length=11, blank=True, verbose_name='SWIFT-код')

    # Корреспондентский счет (может быть несколько для разных валют, но пока сделаем один основной)
    correspondent_account = models.CharField(max_length=20, verbose_name='Корреспондентский счет')

    # Контакты
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    website = models.URLField(blank=True, verbose_name='Сайт')

    # Служебные поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Банк'
        verbose_name_plural = 'Банки'
        ordering = ['name']

    def __str__(self):
        if self.short_name:
            return f"{self.short_name} (БИК: {self.bik})"
        return f"{self.name} (БИК: {self.bik})"
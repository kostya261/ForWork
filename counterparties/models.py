from django.db import models


class Counterparty(models.Model):
    """
    Контрагент (клиент, заказчик, подрядчик).
    """
    # Тип контрагента (опционально, для фильтрации)
    TYPE_CHOICES = (
        ('client', 'Клиент'),
        ('partner', 'Партнер'),
        ('supplier', 'Поставщик'),
    )

    name = models.CharField(max_length=200, verbose_name='Наименование')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='client', verbose_name='Тип')
    description = models.TextField(blank=True, verbose_name='Описание')

    # Контактная информация
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    telegram = models.CharField(max_length=100, blank=True, verbose_name='Telegram')
    whatsapp = models.CharField(max_length=100, blank=True, verbose_name='WhatsApp')

    # Адреса
    legal_address = models.TextField(blank=True, verbose_name='Юридический адрес')
    actual_address = models.TextField(blank=True, verbose_name='Фактический адрес')

    # Реквизиты
    inn = models.CharField(max_length=12, blank=True, verbose_name='ИНН')
    ogrn = models.CharField(max_length=15, blank=True, verbose_name='ОГРН')
    kpp = models.CharField(max_length=9, blank=True, verbose_name='КПП')

    # Банковские реквизиты (может быть несколько счетов, поэтому отдельная модель)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'
        ordering = ['name']

    def __str__(self):
        return self.name


class CounterpartyBankAccount(models.Model):
    """
    Банковские счета контрагента (может быть несколько).
    """
    counterparty = models.ForeignKey(
        Counterparty,
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        verbose_name='Контрагент'
    )
    bank = models.ForeignKey(
        'banks.Bank',
        on_delete=models.PROTECT,
        related_name='counterparty_accounts',
        verbose_name='Банк'
    )
    account_number = models.CharField(max_length=20, verbose_name='Расчетный счет')
    is_primary = models.BooleanField(default=False, verbose_name='Основной счет')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Банковский счет контрагента'
        verbose_name_plural = 'Банковские счета контрагентов'
        unique_together = ['counterparty', 'bank', 'account_number']
        ordering = ['-is_primary', 'bank__name']

    def __str__(self):
        return f"{self.counterparty.name} - {self.bank.name} ({self.account_number})"
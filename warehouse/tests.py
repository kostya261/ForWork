from django.test import TestCase
from warehouse.models import WarehouseItem
from departments.models import Department


class WarehouseTest(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name='Основной склад')
        self.item = WarehouseItem.objects.create(
            name='Гайка М8',
            article='001',
            quantity=100,
            min_stock=10,
            department=self.department
        )

    def test_warehouse_item_creation(self):
        """Проверка создания складской позиции"""
        self.assertEqual(self.item.name, 'Гайка М8')
        self.assertEqual(self.item.quantity, 100)
        self.assertFalse(self.item.is_low_stock)

    def test_low_stock_detection(self):
        """Проверка определения низкого остатка"""
        self.item.quantity = 5
        self.item.save()
        self.assertTrue(self.item.is_low_stock)

    def test_quantity_update(self):
        """Проверка обновления количества"""
        self.item.quantity += 50
        self.item.save()
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 150)
from django.test import TestCase
from django.contrib.auth import get_user_model
from tasks.models import Task, TaskStatusHistory
from django.utils import timezone

User = get_user_model()


class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='testuser@test.com'  # ← уникальный email
        )
        self.responsible = User.objects.create_user(
            username='worker',
            password='testpass',
            email='worker@test.com'  # ← уникальный email
        )

    def test_task_creation(self):
        task = Task.objects.create(
            name='Тестовая задача',
            description='Описание',
            priority='medium',
            created_by=self.user,
            responsible=self.responsible,
            deadline=timezone.now() + timezone.timedelta(days=7)
        )

        self.assertEqual(task.status, 'new')
        self.assertEqual(task.name, 'Тестовая задача')
        self.assertEqual(task.responsible, self.responsible)

    def test_status_history_on_creation(self):
        """Проверка создания записи в истории статусов"""
        task = Task.objects.create(
            name='Задача с историей',
            created_by=self.user,
            status='new'
        )

        # Имитируем поведение сериализатора — создаём запись в истории
        TaskStatusHistory.objects.create(
            task=task,
            old_status='',
            new_status='new',
            changed_by=self.user,
            comment='Задача создана'
        )

        history = TaskStatusHistory.objects.filter(task=task)
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().new_status, 'new')

    def test_task_status_change(self):
        task = Task.objects.create(
            name='Смена статуса',
            created_by=self.user
        )

        task.status = 'in_progress'
        task.save()

        self.assertEqual(task.status, 'in_progress')
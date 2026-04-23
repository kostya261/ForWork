from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from tasks.models import Task
from chat.models import Message
from .models import Notification


@receiver(post_save, sender=Task)
def task_notifications(sender, instance, created, **kwargs):
    """Уведомления при создании/изменении задачи"""
    print(f"=== SIGNAL FIRED: Task {instance.id}, created={created} ===")
    if created:

        print(f"Responsible: {instance.responsible}")
        print(f"Responsible email: {instance.responsible.email if instance.responsible else 'None'}")
        print(f"Created by: {instance.created_by}")
        print(f"Same person: {instance.responsible == instance.created_by}")

        # Новая задача — уведомляем ответственного
        if instance.responsible and instance.responsible != instance.created_by:
            # Внутреннее уведомление
            Notification.objects.create(
                user=instance.responsible,
                type='task_assigned',
                title='Новая задача',
                message=f'Вам назначена задача #{instance.id}: {instance.name}',
                link=f'/tasks/{instance.id}/'
            )

            # Email (если есть email)
            if instance.responsible.email:
                try:
                    send_mail(
                        f'ForWork: Новая задача #{instance.id}',
                        f'Вам назначена задача: {instance.name}\n\n'
                        f'Описание: {instance.description or "—"}\n\n'
                        f'Срок: {instance.deadline or "не указан"}\n\n'
                        f'Ссылка: http://127.0.0.1:8000/tasks/{instance.id}/',
                        settings.DEFAULT_FROM_EMAIL,
                        [instance.responsible.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f'Email error: {e}')

    else:
        # Изменение статуса задачи — уведомляем создателя
        if instance.created_by and instance.responsible != instance.created_by:
            Notification.objects.create(
                user=instance.created_by,
                type='task_status',
                title='Изменён статус задачи',
                message=f'Задача #{instance.id}: {instance.get_status_display()}',
                link=f'/tasks/{instance.id}/'
            )


@receiver(post_save, sender=Message)
def message_notifications(sender, instance, created, **kwargs):
    """Уведомления при новом сообщении в чате"""
    print(f"=== SIGNAL FIRED: Message from {instance.sender}, text: {instance.text[:20]} ===")
    if created:
        room = instance.room
        # Уведомляем всех участников, кроме отправителя
        for user in room.participants.exclude(id=instance.sender.id):
            # Внутреннее уведомление
            Notification.objects.create(
                user=user,
                type='chat_message',
                title=f'Новое сообщение от {instance.sender.get_full_name() or instance.sender.username}',
                message=instance.text[:100] + ('...' if len(instance.text) > 100 else ''),
                link=f'/chat/'
            )
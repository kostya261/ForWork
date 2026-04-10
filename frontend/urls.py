from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Задачи
    path('tasks/', views.task_list, name='tasks_list'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),

    # Инвентарь
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/create/', views.inventory_create, name='inventory_create'),
    path('inventory/<int:pk>/', views.inventory_detail, name='inventory_detail'),
    path('inventory/<int:pk>/edit/', views.inventory_edit, name='inventory_edit'),

    # Склад
    path('warehouse/', views.warehouse_list, name='warehouse_list'),
    path('warehouse/create/', views.warehouse_create, name='warehouse_create'),
    path('warehouse/<int:pk>/', views.warehouse_detail, name='warehouse_detail'),
    path('warehouse/<int:pk>/edit/', views.warehouse_edit, name='warehouse_edit'),

    # Контрагенты
    path('counterparties/', views.counterparty_list, name='counterparties_list'),
    path('counterparties/create/', views.counterparty_create, name='counterparty_create'),
    path('counterparties/<int:pk>/', views.counterparty_detail, name='counterparty_detail'),
    path('counterparties/<int:pk>/edit/', views.counterparty_edit, name='counterparty_edit'),

    # Сотрудники
    path('users/', views.user_list, name='users_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),

    # Остальные

    path('documents/', views.material_requests_list, name='documents_list'),
    path('chat/', views.chat_index, name='chat_index'),
]

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

    # Отделы
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/', views.department_detail, name='department_detail'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),

    # Приходные накладные
    path('documents/receipts/', views.warehouse_receipt_list, name='warehouse_receipt_list'),
    path('documents/receipts/create/', views.warehouse_receipt_create, name='warehouse_receipt_create'),
    path('documents/receipts/<int:pk>/', views.warehouse_receipt_detail, name='warehouse_receipt_detail'),
    path('documents/receipts/<int:pk>/edit/', views.warehouse_receipt_edit, name='warehouse_receipt_edit'),
    path('documents/expenses/', views.warehouse_expense_list, name='warehouse_expense_list'),
    path('documents/expenses/create/', views.warehouse_expense_create, name='warehouse_expense_create'),
    path('documents/expenses/<int:pk>/', views.warehouse_expense_detail, name='warehouse_expense_detail'),
    path('documents/transfers/', views.warehouse_transfer_list, name='warehouse_transfer_list'),
    path('documents/transfers/create/', views.warehouse_transfer_create, name='warehouse_transfer_create'),
    path('documents/transfers/<int:pk>/', views.warehouse_transfer_detail, name='warehouse_transfer_detail'),
    path('documents/stocktakes/', views.warehouse_stocktake_list, name='warehouse_stocktake_list'),
    path('documents/stocktakes/create/', views.warehouse_stocktake_create, name='warehouse_stocktake_create'),
    path('documents/stocktakes/<int:pk>/', views.warehouse_stocktake_detail, name='warehouse_stocktake_detail'),

    # Выдача инвентаря
    path('documents/inventory-issues/', views.inventory_issue_list, name='inventory_issue_list'),
    path('documents/inventory-issues/create/', views.inventory_issue_create, name='inventory_issue_create'),
    path('documents/inventory-issues/<int:pk>/', views.inventory_issue_detail, name='inventory_issue_detail'),

    # Списание ОС
    path('documents/inventory-writeoffs/', views.inventory_writeoff_list, name='inventory_writeoff_list'),
    path('documents/inventory-writeoffs/create/', views.inventory_writeoff_create, name='inventory_writeoff_create'),
    path('documents/inventory-writeoffs/<int:pk>/', views.inventory_writeoff_detail, name='inventory_writeoff_detail'),

    # Перемещение ОС
    path('documents/inventory-transfers/', views.inventory_transfer_list, name='inventory_transfer_list'),
    path('documents/inventory-transfers/create/', views.inventory_transfer_create, name='inventory_transfer_create'),
    path('documents/inventory-transfers/<int:pk>/', views.inventory_transfer_detail, name='inventory_transfer_detail'),

    # Инвентаризация ОС
    path('documents/inventory-stocktakes/', views.inventory_stocktake_list, name='inventory_stocktake_list'),
    path('documents/inventory-stocktakes/create/', views.inventory_stocktake_create, name='inventory_stocktake_create'),
    path('documents/inventory-stocktakes/<int:pk>/', views.inventory_stocktake_detail,
         name='inventory_stocktake_detail'),

    # Наряды на работу
    path('documents/work-orders/', views.work_order_list, name='work_order_list'),
    path('documents/work-orders/create/', views.work_order_create, name='work_order_create'),
    path('documents/work-orders/<int:pk>/', views.work_order_detail, name='work_order_detail'),
    path('documents/work-orders/<int:pk>/edit/', views.work_order_edit, name='work_order_edit'),

    # Акты выполненных работ
    path('documents/completion-acts/', views.completion_act_list, name='completion_act_list'),
    path('documents/completion-acts/create/', views.completion_act_create, name='completion_act_create'),
    path('documents/completion-acts/<int:pk>/', views.completion_act_detail, name='completion_act_detail'),
    path('documents/completion-acts/<int:pk>/edit/', views.completion_act_edit, name='completion_act_edit'),

    # Счета на оплату
    path('documents/invoices/', views.invoice_list, name='invoice_list'),
    path('documents/invoices/create/', views.invoice_create, name='invoice_create'),
    path('documents/invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('documents/invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),

    # Счета-фактуры
    path('documents/invoice-facturas/', views.invoice_factura_list, name='invoice_factura_list'),
    path('documents/invoice-facturas/create/', views.invoice_factura_create, name='invoice_factura_create'),
    path('documents/invoice-facturas/<int:pk>/', views.invoice_factura_detail, name='invoice_factura_detail'),
    path('documents/invoice-facturas/<int:pk>/edit/', views.invoice_factura_edit, name='invoice_factura_edit'),

    # Производители
    path('manufacturers/', views.manufacturer_list, name='manufacturer_list'),
    path('manufacturers/create/', views.manufacturer_create, name='manufacturer_create'),
    path('manufacturers/<int:pk>/edit/', views.manufacturer_edit, name='manufacturer_edit'),

    # Категории
    path('warehouse-categories/', views.warehouse_category_list, name='warehouse_category_list'),
    path('warehouse-categories/create/', views.warehouse_category_create, name='warehouse_category_create'),
    path('warehouse-categories/<int:pk>/edit/', views.warehouse_category_edit, name='warehouse_category_edit'),

    path('inventory-categories/', views.inventory_category_list, name='inventory_category_list'),
    path('inventory-categories/create/', views.inventory_category_create, name='inventory_category_create'),
    path('inventory-categories/<int:pk>/edit/', views.inventory_category_edit, name='inventory_category_edit'),

    # PDF
    path('documents/invoices/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('documents/invoice-facturas/<int:pk>/pdf/', views.invoice_factura_pdf, name='invoice_factura_pdf'),
    path('documents/receipts/<int:pk>/pdf/', views.warehouse_receipt_pdf, name='warehouse_receipt_pdf'),
    path('documents/expenses/<int:pk>/pdf/', views.warehouse_expense_pdf, name='warehouse_expense_pdf'),
    path('documents/completion-acts/<int:pk>/pdf/', views.completion_act_pdf, name='completion_act_pdf'),
    path('documents/work-orders/<int:pk>/pdf/', views.work_order_pdf, name='work_order_pdf'),

    # Чат
    path('chat/', views.chat_index, name='chat_index'),


    # Остальные

    path('documents/', views.material_requests_list, name='documents_list'),

]

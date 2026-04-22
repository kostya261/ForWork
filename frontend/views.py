from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q, F
from django.db.models import Sum
from django.contrib import messages

from categories.models import Category
from inventory_categories.models import InventoryCategory
from manufacturers.models import Manufacturer
from tasks.models import Task, TaskStatusHistory
from tasks.serializers import TaskListSerializer
from counterparties.models import Counterparty
from departments.models import Department
from warehouse.models import WarehouseItem
from inventory.models import InventoryItem
from documents.models import MaterialRequest, InventoryIssue, WarehouseReceipt, WarehouseExpense, WarehouseTransfer, \
    WarehouseStocktake, InventoryWriteOff, InventoryTransfer, InventoryStocktake, WorkOrder, CompletionAct, Invoice, \
    InvoiceFactura
from django.contrib.auth import get_user_model

# PDF
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile

from warehouse_locations.models import WarehouseRack, WarehouseCell

User = get_user_model()


@login_required
def dashboard(request):
    user = request.user
    today = timezone.now().date()

    # Мои задачи
    if user.is_staff or user.is_superuser:
        my_tasks = Task.objects.exclude(
            status__in=['completed', 'closed', 'cancelled']
        ).distinct()
    else:
        my_tasks = Task.objects.filter(
            Q(responsible=user) | Q(co_executors=user) | Q(created_by=user)
        ).exclude(status__in=['completed', 'closed', 'cancelled']).distinct()

    my_tasks_count = my_tasks.count()
    overdue_tasks = my_tasks.filter(deadline__lt=today).count()
    overdue_tasks_list = my_tasks.filter(deadline__lt=today)[:5]

    # Товары с низким остатком
    low_stock_items = WarehouseItem.objects.filter(quantity__lte=F('min_stock'))[:5]
    low_stock = WarehouseItem.objects.filter(quantity__lte=F('min_stock')).count()
    warehouse_items = WarehouseItem.objects.count()

    # Инвентарь
    active_inventory = InventoryItem.objects.filter(status='active', responsible__isnull=False).count()
    available_inventory = InventoryItem.objects.filter(status='active', responsible__isnull=True).count()

    # Документы
    pending_docs = (
        WarehouseReceipt.objects.filter(status='draft').count() +
        WarehouseExpense.objects.filter(status='draft').count() +
        WarehouseTransfer.objects.filter(status='draft').count() +
        WarehouseStocktake.objects.filter(status='draft').count() +
        InventoryIssue.objects.filter(status__in=['draft', 'pending']).count() +
        InventoryWriteOff.objects.filter(status='draft').count() +
        InventoryTransfer.objects.filter(status='draft').count() +
        InventoryStocktake.objects.filter(status='draft').count() +
        WorkOrder.objects.filter(status='draft').count() +
        CompletionAct.objects.filter(status='draft').count() +
        Invoice.objects.filter(status='draft').count() +
        InvoiceFactura.objects.filter(status='draft').count() +
        MaterialRequest.objects.filter(status__in=['draft', 'pending']).count()
    )

    # Последние задачи
    recent_tasks = my_tasks.order_by('-created_at')[:10]

    # ЖИВАЯ ЛЕНТА АКТИВНОСТИ
    recent_activities = []

    # Последние приходы
    for receipt in WarehouseReceipt.objects.select_related('supplier').filter(status='conducted').order_by('-created_at')[:3]:
        recent_activities.append({
            'time': receipt.created_at,
            'text': f'📥 Приход №{receipt.number} от {receipt.supplier.name} на {receipt.total_sum:.2f} ₽',
            'link': f'/documents/receipts/{receipt.pk}/'
        })

    # Последние расходы
    for expense in WarehouseExpense.objects.select_related('counterparty').filter(status='conducted').order_by('-created_at')[:3]:
        name = expense.counterparty.name if expense.counterparty else 'внутреннее списание'
        recent_activities.append({
            'time': expense.created_at,
            'text': f'📤 Расход №{expense.number} ({name}) на {expense.total_sum:.2f} ₽',
            'link': f'/documents/expenses/{expense.pk}/'
        })

    # Последние перемещения
    for transfer in WarehouseTransfer.objects.select_related('from_department', 'to_department').filter(status='conducted').order_by('-created_at')[:3]:
        recent_activities.append({
            'time': transfer.created_at,
            'text': f'🔄 Перемещение №{transfer.number}: {transfer.from_department.name} → {transfer.to_department.name}',
            'link': f'/documents/transfers/{transfer.pk}/'
        })

    # Новые задачи
    for task in Task.objects.order_by('-created_at')[:3]:
        recent_activities.append({
            'time': task.created_at,
            'text': f'📋 Задача #{task.pk}: {task.name[:50]}{"..." if len(task.name) > 50 else ""}',
            'link': f'/tasks/{task.pk}/'
        })

    # Изменения статусов задач
    for history in TaskStatusHistory.objects.select_related('task', 'changed_by').order_by('-created_at')[:3]:
        recent_activities.append({
            'time': history.created_at,
            'text': f'🔄 Задача #{history.task.pk}: {history.get_new_status_display()}',
            'link': f'/tasks/{history.task.pk}/'
        })

    # Новые счета
    for invoice in Invoice.objects.select_related('counterparty').order_by('-created_at')[:3]:
        recent_activities.append({
            'time': invoice.created_at,
            'text': f'🧾 Счёт №{invoice.number} для {invoice.counterparty.name} на {invoice.total_sum:.2f} ₽',
            'link': f'/documents/invoices/{invoice.pk}/'
        })

    # Сортируем и берём последние 10
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    recent_activities = recent_activities[:10]

    context = {
        'today': today,
        'my_tasks_count': my_tasks_count,
        'overdue_tasks': overdue_tasks,
        'warehouse_items': warehouse_items,
        'low_stock': low_stock,
        'low_stock_items': low_stock_items,
        'active_inventory': active_inventory,
        'available_inventory': available_inventory,
        'pending_docs': pending_docs,
        'recent_tasks': recent_tasks,
        'overdue_tasks_list': overdue_tasks_list,
        'recent_activities': recent_activities,
    }

    return render(request, 'frontend/dashboard.html', context)


@login_required
def task_list(request):
    """Список задач с фильтрацией"""
    user = request.user

    # Базовый queryset
    tasks = Task.objects.all().select_related(
        'responsible', 'department', 'counterparty', 'created_by'
    ).prefetch_related('co_executors')

    # Если не админ — показываем только задачи своего отдела или где пользователь участник
    if not user.is_staff and not user.is_superuser:
        tasks = tasks.filter(
            Q(department=user.department) |
            Q(responsible=user) |
            Q(co_executors=user) |
            Q(created_by=user)
        ).distinct()

    # Фильтры из GET-параметров
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    my_only = request.GET.get('my', '')
    search_query = request.GET.get('search', '')
    overdue = request.GET.get('overdue', '')

    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    '''    if my_only == 'true':
        tasks = tasks.filter(responsible=user)'''
    if my_only == 'true':
        tasks = tasks.filter(
            Q(responsible=user) |
            Q(co_executors=user) |
            Q(created_by=user)).distinct()
    if overdue == 'true':
        tasks = tasks.filter(deadline__lt=timezone.now()).exclude(status__in=['completed', 'closed', 'cancelled'])
    if search_query:
        tasks = tasks.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    # Статистика для шапки
    stats = {
        'total': tasks.count(),
        'new': tasks.filter(status='new').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'completed': tasks.filter(status='completed').count(),
        'overdue': tasks.filter(deadline__lt=timezone.now()).exclude(
            status__in=['completed', 'closed', 'cancelled']).count(),
    }

    # Пагинация (простая, без DRF)
    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(tasks, 20)
    tasks_page = paginator.get_page(page)

    context = {
        'tasks': tasks_page,
        'stats': stats,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'current_filters': {
            'status': status_filter,
            'priority': priority_filter,
            'my': my_only,
            'search': search_query,
        }
    }

    return render(request, 'frontend/task_list.html', context)


@login_required
def task_detail(request, pk):
    """Детальная страница задачи"""
    task = get_object_or_404(
        Task.objects.select_related(
            'responsible', 'department', 'counterparty', 'created_by'
        ).prefetch_related(
            'co_executors', 'comments__author',
            'inventory_requirements__inventory',
            'material_requirements__warehouse_item'
        ),
        pk=pk
    )

    context = {
        'task': task,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
    }

    return render(request, 'frontend/task_detail.html', context)


@login_required
def task_create(request):
    """Создание новой задачи"""
    if request.method == 'POST':
        # Здесь будет обработка формы
        pass

    context = {
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
    }

    return render(request, 'frontend/task_form.html', context)


@login_required
def inventory_list(request):
    """Список инвентаря"""
    items = InventoryItem.objects.all().select_related(
        'manufacturer', 'department', 'responsible', 'category'
    )

    # Фильтры
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    my_only = request.GET.get('my', '')

    if status_filter:
        items = items.filter(status=status_filter)
    if category_filter:
        try:
            from inventory_categories.models import InventoryCategory
            category = InventoryCategory.objects.get(id=category_filter)
            descendants = category.get_descendants(include_self=True)
            items = items.filter(category__in=descendants)
        except InventoryCategory.DoesNotExist:
            pass
    if my_only == 'true':
        items = items.filter(responsible=request.user)
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(inventory_number__icontains=search_query) |
            Q(serial_number__icontains=search_query)
        )

    # Статистика
    stats = {
        'total': items.count(),
        'active': items.filter(status='active').count(),
        'repair': items.filter(status='repair').count(),
        'decommissioned': items.filter(status='decommissioned').count(),
    }

    # Категории для фильтра
    from inventory_categories.models import InventoryCategory
    categories = InventoryCategory.objects.all()

    # Пагинация
    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(items, 20)
    items_page = paginator.get_page(page)

    context = {
        'items': items_page,
        'stats': stats,
        'categories': categories,
        'status_choices': InventoryItem.STATUS_CHOICES,
        'current_filters': {
            'status': status_filter,
            'category': category_filter,
            'my': my_only,
            'search': search_query,
        }
    }

    return render(request, 'frontend/inventory_list.html', context)


@login_required
def inventory_detail(request, pk):
    """Детальная страница инвентаря"""
    item = get_object_or_404(
        InventoryItem.objects.select_related(
            'manufacturer', 'department', 'responsible', 'category'
        ),
        pk=pk
    )

    context = {
        'item': item,
        'status_choices': InventoryItem.STATUS_CHOICES,
    }

    return render(request, 'frontend/inventory_detail.html', context)


@login_required
def inventory_create(request):
    """Создание инвентаря"""
    if request.method == 'POST':
        # Будет обрабатываться через JS
        pass

    from inventory_categories.models import InventoryCategory
    from manufacturers.models import Manufacturer
    from departments.models import Department

    context = {
        'status_choices': InventoryItem.STATUS_CHOICES,
        'categories': InventoryCategory.objects.all(),
        'manufacturers': Manufacturer.objects.all(),
        'departments': Department.objects.all(),
    }

    return render(request, 'frontend/inventory_form.html', context)


@login_required
def inventory_edit(request, pk):
    """Редактирование инвентаря"""
    item = get_object_or_404(InventoryItem, pk=pk)

    from inventory_categories.models import InventoryCategory
    from manufacturers.models import Manufacturer
    from departments.models import Department

    context = {
        'item': item,
        'status_choices': InventoryItem.STATUS_CHOICES,
        'categories': InventoryCategory.objects.all(),
        'manufacturers': Manufacturer.objects.all(),
        'departments': Department.objects.all(),
    }

    return render(request, 'frontend/inventory_form.html', context)


@login_required
def warehouse_list(request):
    """Список складских позиций с выбором склада"""
    user = request.user
    items = WarehouseItem.objects.all().select_related(
        'category', 'manufacturer', 'department', 'cell', 'cell__rack'
    )

    # Определяем доступные отделы (склады)
    if user.is_staff or user.is_superuser:
        available_departments = Department.objects.all()
    else:
        # Обычный пользователь видит только свой отдел
        available_departments = Department.objects.filter(
            id=user.department_id) if user.department else Department.objects.none()

    # Фильтр по отделу (складу)
    department_filter = request.GET.get('department', '')

    if department_filter:
        # Проверяем, что пользователь имеет доступ к выбранному складу
        if available_departments.filter(id=department_filter).exists():
            items = items.filter(department_id=department_filter)
        else:
            # Если нет доступа — показываем первый доступный
            first_dept = available_departments.first()
            if first_dept:
                items = items.filter(department=first_dept)
                department_filter = str(first_dept.id)
    else:
        # По умолчанию — первый доступный склад
        first_dept = available_departments.first()
        if first_dept:
            items = items.filter(department=first_dept)
            department_filter = str(first_dept.id)

    # Остальные фильтры
    category_filter = request.GET.get('category', '')
    manufacturer_filter = request.GET.get('manufacturer', '')
    search_query = request.GET.get('search', '')
    low_stock_only = request.GET.get('low_stock', '')

    if category_filter:
        try:
            from categories.models import Category
            category = Category.objects.get(id=category_filter)
            descendants = category.get_descendants(include_self=True)
            items = items.filter(category__in=descendants)
        except Category.DoesNotExist:
            pass

    if manufacturer_filter:
        items = items.filter(manufacturer_id=manufacturer_filter)

    if low_stock_only == 'true':
        items = items.filter(quantity__lte=F('min_stock'))

    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(article__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Статистика (по отфильтрованным товарам)
    stats = {
        'total': items.count(),
        'total_quantity': items.aggregate(sum=Sum('quantity'))['sum'] or 0,
        'low_stock': items.filter(quantity__lte=F('min_stock')).count(),
        'categories': items.values('category').distinct().count(),
    }

    # Категории и производители для фильтров (только те, что есть на выбранном складе)
    from categories.models import Category
    from manufacturers.models import Manufacturer

    # Категории, которые есть в отфильтрованных товарах
    used_category_ids = items.values_list('category_id', flat=True).distinct()
    categories = Category.objects.filter(id__in=used_category_ids)

    # Производители, которые есть в отфильтрованных товарах
    used_manufacturer_ids = items.values_list('manufacturer_id', flat=True).distinct()
    manufacturers = Manufacturer.objects.filter(id__in=used_manufacturer_ids)

    # Пагинация
    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(items, 20)
    items_page = paginator.get_page(page)

    context = {
        'items': items_page,
        'stats': stats,
        'categories': categories,
        'manufacturers': manufacturers,
        'departments': available_departments,  # Все доступные склады для переключателя
        'current_filters': {
            'department': department_filter,
            'category': category_filter,
            'manufacturer': manufacturer_filter,
            'low_stock': low_stock_only,
            'search': search_query,
        }
    }

    return render(request, 'frontend/warehouse_list.html', context)


@login_required
def warehouse_detail(request, pk):
    """Детальная страница складской позиции"""
    item = get_object_or_404(
        WarehouseItem.objects.select_related(
            'category', 'manufacturer', 'department'
        ).prefetch_related('transactions'),
        pk=pk
    )

    context = {
        'item': item,
        'transactions': item.transactions.order_by('-created_at')[:20],
    }

    return render(request, 'frontend/warehouse_detail.html', context)


@login_required
def warehouse_create(request):
    """Создание складской позиции"""
    from categories.models import Category
    from manufacturers.models import Manufacturer
    from departments.models import Department

    cells = WarehouseCell.objects.all().select_related('rack')

    context = {
        'categories': Category.objects.all(),
        'manufacturers': Manufacturer.objects.all(),
        'departments': Department.objects.all(),
        'cells': cells,
        'unit_choices': WarehouseItem.UNIT_CHOICES,
    }

    return render(request, 'frontend/warehouse_form.html', context)


@login_required
def warehouse_edit(request, pk):
    item = get_object_or_404(WarehouseItem, pk=pk)

    from categories.models import Category
    from manufacturers.models import Manufacturer
    from departments.models import Department

    # 🔥 Только ячейки отдела этого товара
    cells = WarehouseCell.objects.filter(
        rack__department=item.department
    ).select_related('rack')

    context = {
        'item': item,
        'categories': Category.objects.all(),
        'manufacturers': Manufacturer.objects.all(),
        'departments': Department.objects.all(),
        'cells': cells,
        'unit_choices': WarehouseItem.UNIT_CHOICES,
    }
    return render(request, 'frontend/warehouse_form.html', context)


@login_required
def counterparty_list(request):
    """Список контрагентов"""
    counterparties = Counterparty.objects.all().prefetch_related('bank_accounts__bank')

    # Фильтры
    type_filter = request.GET.get('type', '')
    search_query = request.GET.get('search', '')

    if type_filter:
        counterparties = counterparties.filter(type=type_filter)
    if search_query:
        counterparties = counterparties.filter(
            Q(name__icontains=search_query) |
            Q(inn__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Статистика
    stats = {
        'total': counterparties.count(),
        'clients': counterparties.filter(type='client').count(),
        'partners': counterparties.filter(type='partner').count(),
        'suppliers': counterparties.filter(type='supplier').count(),
    }

    # Пагинация
    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(counterparties, 20)
    items_page = paginator.get_page(page)

    context = {
        'counterparties': items_page,
        'stats': stats,
        'type_choices': Counterparty.TYPE_CHOICES,
        'current_filters': {
            'type': type_filter,
            'search': search_query,
        }
    }

    return render(request, 'frontend/counterparty_list.html', context)


@login_required
def counterparty_detail(request, pk):
    """Детальная страница контрагента"""
    counterparty = get_object_or_404(
        Counterparty.objects.prefetch_related('bank_accounts__bank', 'tasks'),
        pk=pk
    )

    context = {
        'counterparty': counterparty,
        'tasks': counterparty.tasks.order_by('-created_at')[:10],
    }

    return render(request, 'frontend/counterparty_detail.html', context)


@login_required
def counterparty_create(request):
    """Создание контрагента"""
    context = {
        'type_choices': Counterparty.TYPE_CHOICES,
    }
    return render(request, 'frontend/counterparty_form.html', context)


@login_required
def counterparty_edit(request, pk):
    """Редактирование контрагента"""
    counterparty = get_object_or_404(Counterparty, pk=pk)

    context = {
        'counterparty': counterparty,
        'type_choices': Counterparty.TYPE_CHOICES,
    }

    return render(request, 'frontend/counterparty_form.html', context)


@login_required
def user_list(request):
    """Список сотрудников"""
    users = User.objects.all().select_related('position', 'department', 'photo')

    # Фильтры
    department_filter = request.GET.get('department', '')
    position_filter = request.GET.get('position', '')
    search_query = request.GET.get('search', '')
    active_only = request.GET.get('active', '')

    if department_filter:
        users = users.filter(department_id=department_filter)
    if position_filter:
        users = users.filter(position_id=position_filter)
    if active_only == 'true':
        users = users.filter(is_active=True)
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(middle_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    # Статистика
    stats = {
        'total': users.count(),
        'active': users.filter(is_active=True).count(),
        'staff': users.filter(is_staff=True).count(),
        'with_transport': users.filter(has_transport=True).count(),
    }

    # Справочники для фильтров
    from departments.models import Department
    from positions.models import Position
    departments = Department.objects.all()
    positions = Position.objects.all()

    # Пагинация
    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(users, 20)
    users_page = paginator.get_page(page)

    context = {
        'users': users_page,
        'stats': stats,
        'departments': departments,
        'positions': positions,
        'current_filters': {
            'department': department_filter,
            'position': position_filter,
            'active': active_only,
            'search': search_query,
        }
    }

    return render(request, 'frontend/user_list.html', context)


@login_required
def user_detail(request, pk):
    """Детальная страница сотрудника"""
    user = get_object_or_404(
        User.objects.select_related('position', 'department', 'photo'),
        pk=pk
    )

    # Задачи, где ответственный
    responsible_tasks = user.responsible_tasks.order_by('-created_at')[:10]
    # Задачи, где соисполнитель
    co_tasks = user.co_executed_tasks.order_by('-created_at')[:10]
    # Инвентарь на руках
    inventory = user.responsible_inventory.filter(status='active')

    context = {
        'employee': user,
        'responsible_tasks': responsible_tasks,
        'co_tasks': co_tasks,
        'inventory': inventory,
    }

    return render(request, 'frontend/user_detail.html', context)


@login_required
def chat_index(request):
    """Страница чата"""
    return render(request, 'frontend/chat.html')


@login_required
def department_list(request):
    """Список отделов (дерево)"""
    departments = Department.objects.all().select_related('parent', 'head')

    # Строим дерево
    def build_tree(parent=None):
        result = []
        for dept in departments.filter(parent=parent):
            result.append({
                'id': dept.id,
                'name': dept.name,
                'description': dept.description,
                'head': dept.head,
                'legal_address': dept.legal_address,
                'actual_address': dept.actual_address,
                'children': build_tree(dept)
            })
        return result

    tree = build_tree()

    context = {
        'departments': departments,
        'tree': tree,
    }

    return render(request, 'frontend/department_list.html', context)


@login_required
def department_detail(request, pk):
    """Детальная страница отдела"""
    department = get_object_or_404(Department, pk=pk)
    employees = department.users.all().select_related('position')

    context = {
        'department': department,
        'employees': employees,
    }

    return render(request, 'frontend/department_detail.html', context)


@login_required
def department_create(request):
    parents = Department.objects.all()
    users = User.objects.filter(is_active=True)
    context = {'parents': parents, 'users': users}
    return render(request, 'frontend/department_form.html', context)


@login_required
def department_edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    parents = Department.objects.exclude(pk=pk)  # исключаем сам себя
    users = User.objects.filter(is_active=True)
    context = {'department': department, 'parents': parents, 'users': users}
    return render(request, 'frontend/department_form.html', context)


# Работа с документацией

@login_required
def warehouse_receipt_list(request):
    """Список приходных накладных"""
    receipts = WarehouseReceipt.objects.all().select_related('supplier', 'department', 'created_by')

    # Фильтры
    status_filter = request.GET.get('status', '')
    supplier_filter = request.GET.get('supplier', '')
    search_query = request.GET.get('search', '')

    if status_filter:
        receipts = receipts.filter(status=status_filter)
    if supplier_filter:
        receipts = receipts.filter(supplier_id=supplier_filter)
    if search_query:
        receipts = receipts.filter(
            Q(number__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )

    # Статистика
    stats = {
        'total': receipts.count(),
        'draft': receipts.filter(status='draft').count(),
        'conducted': receipts.filter(status='conducted').count(),
    }

    # Справочники для фильтров
    suppliers = Counterparty.objects.filter(type__in=['supplier', 'client', 'partner'])

    # Пагинация
    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(receipts, 20)
    receipts_page = paginator.get_page(page)

    context = {
        'receipts': receipts_page,
        'stats': stats,
        'suppliers': suppliers,
        'current_filters': {
            'status': status_filter,
            'supplier': supplier_filter,
            'search': search_query,
        }
    }

    return render(request, 'frontend/warehouse_receipt_list.html', context)


@login_required
def warehouse_receipt_detail(request, pk):
    """Детальная страница приходной накладной"""
    receipt = get_object_or_404(
        WarehouseReceipt.objects.select_related('supplier', 'department', 'created_by', 'conducted_by')
        .prefetch_related('items__warehouse_item'),
        pk=pk
    )

    context = {
        'receipt': receipt,
    }

    return render(request, 'frontend/warehouse_receipt_detail.html', context)


@login_required
def warehouse_receipt_create(request):
    """Создание приходной накладной"""
    suppliers = Counterparty.objects.filter(type__in=['supplier', 'client', 'partner'])
    departments = Department.objects.all()
    warehouse_items = WarehouseItem.objects.all()

    context = {
        'suppliers': suppliers,
        'departments': departments,
        'warehouse_items': warehouse_items,
    }

    return render(request, 'frontend/warehouse_receipt_form.html', context)


@login_required
def warehouse_receipt_edit(request, pk):
    """Редактирование приходной накладной"""
    receipt = get_object_or_404(WarehouseReceipt, pk=pk)

    # Редактировать можно только черновики
    if receipt.status != 'draft':
        messages.error(request, 'Можно редактировать только черновики')
        return redirect('frontend:warehouse_receipt_detail', pk=pk)

    suppliers = Counterparty.objects.filter(type__in=['supplier', 'client', 'partner'])
    departments = Department.objects.all()
    warehouse_items = WarehouseItem.objects.all()

    context = {
        'receipt': receipt,
        'suppliers': suppliers,
        'departments': departments,
        'warehouse_items': warehouse_items,
    }

    return render(request, 'frontend/warehouse_receipt_form.html', context)


# Остальные заглушки

@login_required
def material_requests_list(request):
    return render(request, 'frontend/stub.html', {'title': 'Документы'})


@login_required
def task_edit(request, pk):
    """Редактирование задачи"""
    task = get_object_or_404(Task, pk=pk)

    context = {
        'task': task,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
    }

    return render(request, 'frontend/task_edit.html', context)


@login_required
def warehouse_expense_list(request):
    expenses = WarehouseExpense.objects.all().select_related('department', 'counterparty', 'created_by')

    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    if status_filter:
        expenses = expenses.filter(status=status_filter)
    if search_query:
        expenses = expenses.filter(
            Q(number__icontains=search_query) |
            Q(counterparty__name__icontains=search_query)
        )

    stats = {
        'total': expenses.count(),
        'draft': expenses.filter(status='draft').count(),
        'conducted': expenses.filter(status='conducted').count(),
    }

    return render(request, 'frontend/warehouse_expense_list.html', {
        'expenses': expenses,
        'stats': stats,
        'current_filters': {'status': status_filter, 'search': search_query}
    })


@login_required
def warehouse_expense_detail(request, pk):
    expense = get_object_or_404(WarehouseExpense.objects.select_related('department', 'counterparty', 'created_by',
                                                                        'conducted_by').prefetch_related(
        'items__warehouse_item'), pk=pk)
    return render(request, 'frontend/warehouse_expense_detail.html', {'expense': expense})


@login_required
def warehouse_expense_create(request):
    departments = Department.objects.all()
    counterparties = Counterparty.objects.all()
    warehouse_items = WarehouseItem.objects.all()
    tasks = Task.objects.filter(status__in=['new', 'assigned', 'in_progress'])
    return render(request, 'frontend/warehouse_expense_form.html',
                  {'departments': departments, 'counterparties': counterparties,
                   'warehouse_items': warehouse_items, 'tasks': tasks})


@login_required
def warehouse_transfer_list(request):
    transfers = WarehouseTransfer.objects.all().select_related('from_department', 'to_department', 'created_by')

    # 🔥 Добавляем фильтр по статусу
    status_filter = request.GET.get('status', '')
    if status_filter:
        transfers = transfers.filter(status=status_filter)

    stats = {
        'total': transfers.count(),
        'draft': transfers.filter(status='draft').count(),
        'conducted': transfers.filter(status='conducted').count(),
    }

    return render(request, 'frontend/warehouse_transfer_list.html', {
        'transfers': transfers,
        'stats': stats,
        'current_filters': {'status': status_filter}  # 🔥 для подсветки активного фильтра
    })


@login_required
def warehouse_transfer_detail(request, pk):
    transfer = get_object_or_404(
        WarehouseTransfer.objects.select_related('from_department', 'to_department', 'created_by',
                                                 'conducted_by').prefetch_related('items__warehouse_item'), pk=pk)
    return render(request, 'frontend/warehouse_transfer_detail.html', {'transfer': transfer})


@login_required
def warehouse_transfer_create(request):
    user = request.user
    departments = Department.objects.all()

    # 🔥 По умолчанию показываем товары первого доступного склада
    # или склада пользователя
    if user.is_staff or user.is_superuser:
        default_dept = departments.first()
    else:
        default_dept = user.department

    warehouse_items = WarehouseItem.objects.filter(
        department=default_dept) if default_dept else WarehouseItem.objects.none()

    return render(request, 'frontend/warehouse_transfer_form.html',
                  {'departments': departments, 'warehouse_items': warehouse_items, 'default_department': default_dept})


@login_required
def warehouse_stocktake_list(request):
    stocktakes = WarehouseStocktake.objects.all().select_related('department', 'created_by')

    # 🔥 Добавляем фильтр по статусу
    status_filter = request.GET.get('status', '')
    if status_filter:
        stocktakes = stocktakes.filter(status=status_filter)

    stats = {
        'total': stocktakes.count(),
        'draft': stocktakes.filter(status='draft').count(),
        'conducted': stocktakes.filter(status='conducted').count(),
    }

    return render(request, 'frontend/warehouse_stocktake_list.html', {
        'stocktakes': stocktakes,
        'stats': stats,
        'current_filters': {'status': status_filter}
    })


@login_required
def warehouse_stocktake_detail(request, pk):
    stocktake = get_object_or_404(
        WarehouseStocktake.objects.select_related('department', 'created_by', 'conducted_by').prefetch_related(
            'items__warehouse_item'), pk=pk)
    return render(request, 'frontend/warehouse_stocktake_detail.html', {'stocktake': stocktake})


@login_required
def warehouse_stocktake_create(request):
    departments = Department.objects.all()
    warehouse_items = WarehouseItem.objects.all()
    return render(request, 'frontend/warehouse_stocktake_form.html',
                  {'departments': departments, 'warehouse_items': warehouse_items})


@login_required
def inventory_issue_list(request):
    issues = InventoryIssue.objects.all().select_related('department', 'task', 'created_by')

    status_filter = request.GET.get('status', '')
    if status_filter:
        issues = issues.filter(status=status_filter)

    stats = {
        'total': issues.count(),
        'draft': issues.filter(status='draft').count(),
        'issued': issues.filter(status='issued').count(),
        'returned': issues.filter(status='returned').count(),
    }

    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(issues, 20)
    issues_page = paginator.get_page(page)

    context = {
        'issues': issues_page,
        'stats': stats,
        'current_filters': {'status': status_filter},
    }
    return render(request, 'frontend/inventory_issue_list.html', context)


@login_required
def inventory_issue_detail(request, pk):
    """Детальная страница выдачи инвентаря"""
    issue = get_object_or_404(
        InventoryIssue.objects.select_related('department', 'task', 'created_by', 'approved_by', 'issued_by')
        .prefetch_related('items__inventory_item', 'items__responsible'),
        pk=pk
    )
    return render(request, 'frontend/inventory_issue_detail.html', {'issue': issue})


@login_required
def inventory_issue_create(request):
    """Создание выдачи инвентаря"""
    departments = Department.objects.all()
    tasks = Task.objects.filter(status__in=['new', 'assigned', 'in_progress'])
    inventory_items = InventoryItem.objects.filter(status='active')  # ← убрал responsible__isnull
    users = User.objects.filter(is_active=True)

    context = {
        'departments': departments,
        'tasks': tasks,
        'inventory_items': inventory_items,
        'users': users,
    }
    return render(request, 'frontend/inventory_issue_form.html', context)


@login_required
def inventory_writeoff_list(request):
    writeoffs = InventoryWriteOff.objects.all().select_related('department', 'created_by')

    status_filter = request.GET.get('status', '')
    if status_filter:
        writeoffs = writeoffs.filter(status=status_filter)

    stats = {
        'total': writeoffs.count(),
        'draft': writeoffs.filter(status='draft').count(),
        'conducted': writeoffs.filter(status='conducted').count(),
    }

    return render(request, 'frontend/inventory_writeoff_list.html', {
        'writeoffs': writeoffs,
        'stats': stats,
        'current_filters': {'status': status_filter}
    })


@login_required
def inventory_writeoff_detail(request, pk):
    writeoff = get_object_or_404(
        InventoryWriteOff.objects.select_related('department', 'created_by', 'conducted_by').prefetch_related(
            'items__inventory_item'), pk=pk)
    return render(request, 'frontend/inventory_writeoff_detail.html', {'writeoff': writeoff})


@login_required
def inventory_writeoff_create(request):
    departments = Department.objects.all()
    inventory_items = InventoryItem.objects.filter(status='active')
    return render(request, 'frontend/inventory_writeoff_form.html',
                  {'departments': departments, 'inventory_items': inventory_items})


@login_required
def inventory_transfer_list(request):
    transfers = InventoryTransfer.objects.all().select_related('from_department', 'to_department', 'created_by')

    status_filter = request.GET.get('status', '')
    if status_filter:
        transfers = transfers.filter(status=status_filter)

    stats = {
        'total': transfers.count(),
        'draft': transfers.filter(status='draft').count(),
        'conducted': transfers.filter(status='conducted').count(),
    }

    return render(request, 'frontend/inventory_transfer_list.html', {
        'transfers': transfers,
        'stats': stats,
        'current_filters': {'status': status_filter}
    })


@login_required
def inventory_transfer_detail(request, pk):
    transfer = get_object_or_404(
        InventoryTransfer.objects.select_related('from_department', 'to_department', 'created_by',
                                                 'conducted_by').prefetch_related('items__inventory_item',
                                                                                  'items__new_responsible'), pk=pk)
    return render(request, 'frontend/inventory_transfer_detail.html', {'transfer': transfer})


@login_required
def inventory_transfer_create(request):
    departments = Department.objects.all()
    inventory_items = InventoryItem.objects.filter(status='active')
    users = User.objects.filter(is_active=True)
    return render(request, 'frontend/inventory_transfer_form.html',
                  {'departments': departments, 'inventory_items': inventory_items, 'users': users})


@login_required
def inventory_stocktake_list(request):
    stocktakes = InventoryStocktake.objects.all().select_related('department', 'created_by')

    status_filter = request.GET.get('status', '')
    if status_filter:
        stocktakes = stocktakes.filter(status=status_filter)

    stats = {
        'total': stocktakes.count(),
        'draft': stocktakes.filter(status='draft').count(),
        'conducted': stocktakes.filter(status='conducted').count(),
    }

    return render(request, 'frontend/inventory_stocktake_list.html', {
        'stocktakes': stocktakes,
        'stats': stats,
        'current_filters': {'status': status_filter}
    })


@login_required
def inventory_stocktake_detail(request, pk):
    stocktake = get_object_or_404(
        InventoryStocktake.objects.select_related('department', 'created_by', 'conducted_by').prefetch_related(
            'items__inventory_item'), pk=pk)
    return render(request, 'frontend/inventory_stocktake_detail.html', {'stocktake': stocktake})


@login_required
def inventory_stocktake_create(request):
    departments = Department.objects.all()
    inventory_items = InventoryItem.objects.filter(status='active')
    return render(request, 'frontend/inventory_stocktake_form.html',
                  {'departments': departments, 'inventory_items': inventory_items})


@login_required
def work_order_list(request):
    orders = WorkOrder.objects.all().select_related('task', 'created_by')

    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    if status_filter:
        orders = orders.filter(status=status_filter)
    if search_query:
        orders = orders.filter(
            Q(number__icontains=search_query) |
            Q(task__name__icontains=search_query)
        )

    stats = {
        'total': orders.count(),
        'draft': orders.filter(status='draft').count(),
        'issued': orders.filter(status='issued').count(),
    }

    return render(request, 'frontend/work_order_list.html', {
        'orders': orders,
        'stats': stats,
        'current_filters': {'status': status_filter, 'search': search_query}
    })


@login_required
def work_order_detail(request, pk):
    order = get_object_or_404(WorkOrder.objects.select_related('task', 'created_by', 'issued_by').prefetch_related(
        'materials__warehouse_item', 'inventory__inventory_item'), pk=pk)
    return render(request, 'frontend/work_order_detail.html', {'order': order})


@login_required
def work_order_create(request):
    tasks = Task.objects.filter(status__in=['new', 'assigned', 'in_progress'])
    warehouse_items = WarehouseItem.objects.all()
    inventory_items = InventoryItem.objects.filter(status='active')
    users = User.objects.filter(is_active=True)  # ← обязательно
    return render(request, 'frontend/work_order_form.html', {
        'tasks': tasks,
        'warehouse_items': warehouse_items,
        'inventory_items': inventory_items,
        'users': users,
    })


@login_required
def completion_act_list(request):
    acts = CompletionAct.objects.all().select_related('task', 'created_by')

    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    if status_filter:
        acts = acts.filter(status=status_filter)
    if search_query:
        acts = acts.filter(
            Q(number__icontains=search_query) |
            Q(task__name__icontains=search_query)
        )

    stats = {
        'total': acts.count(),
        'draft': acts.filter(status='draft').count(),
        'signed': acts.filter(status='signed').count(),
    }

    return render(request, 'frontend/completion_act_list.html', {
        'acts': acts,
        'stats': stats,
        'current_filters': {'status': status_filter, 'search': search_query}
    })


@login_required
def completion_act_detail(request, pk):
    act = get_object_or_404(
        CompletionAct.objects.select_related('task', 'work_order', 'created_by', 'signed_by').prefetch_related(
            'materials__warehouse_item'), pk=pk)
    return render(request, 'frontend/completion_act_detail.html', {'act': act})


@login_required
def completion_act_create(request):
    tasks = Task.objects.filter(status__in=['in_progress', 'completed'])
    work_orders = WorkOrder.objects.filter(status='issued')
    warehouse_items = WarehouseItem.objects.all()
    return render(request, 'frontend/completion_act_form.html', {
        'tasks': tasks, 'work_orders': work_orders, 'warehouse_items': warehouse_items
    })


@login_required
def completion_act_edit(request, pk):
    act = get_object_or_404(CompletionAct, pk=pk)
    if act.status != 'draft':
        messages.error(request, 'Можно редактировать только черновик')
        return redirect('frontend:completion_act_detail', pk=pk)

    tasks = Task.objects.filter(pk=act.task_id)
    work_orders = WorkOrder.objects.filter(task_id=act.task_id, status='issued')
    warehouse_items = WarehouseItem.objects.all()

    return render(request, 'frontend/completion_act_form.html', {
        'act': act,
        'tasks': tasks,
        'work_orders': work_orders,
        'warehouse_items': warehouse_items,
    })


@login_required
def work_order_edit(request, pk):
    order = get_object_or_404(WorkOrder, pk=pk)
    if order.status != 'draft':
        messages.error(request, 'Можно редактировать только черновик')
        return redirect('frontend:work_order_detail', pk=pk)

    tasks = Task.objects.filter(pk=order.task_id)
    warehouse_items = WarehouseItem.objects.all()
    inventory_items = InventoryItem.objects.filter(status='active')
    users = User.objects.filter(is_active=True)

    return render(request, 'frontend/work_order_form.html', {
        'order': order,
        'tasks': tasks,
        'warehouse_items': warehouse_items,
        'inventory_items': inventory_items,
        'users': users,
    })


@login_required
def invoice_list(request):
    invoices = Invoice.objects.all().select_related('counterparty', 'created_by')

    status_filter = request.GET.get('status', '')
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    stats = {
        'total': invoices.count(),
        'draft': invoices.filter(status='draft').count(),
        'sent': invoices.filter(status='sent').count(),
        'paid': invoices.filter(status='paid').count(),
    }

    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(invoices, 20)
    invoices_page = paginator.get_page(page)

    return render(request, 'frontend/invoice_list.html', {
        'invoices': invoices_page,
        'stats': stats,
        'current_filters': {'status': status_filter}
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related('counterparty', 'task', 'created_by')
        .prefetch_related('items__warehouse_item'),
        pk=pk
    )
    return render(request, 'frontend/invoice_detail.html', {'invoice': invoice})


@login_required
def invoice_create(request):
    counterparties = Counterparty.objects.all()
    tasks = Task.objects.filter(status__in=['new', 'assigned', 'in_progress', 'completed'])
    warehouse_items = WarehouseItem.objects.all()

    return render(request, 'frontend/invoice_form.html', {
        'counterparties': counterparties,
        'tasks': tasks,
        'warehouse_items': warehouse_items,
    })


@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status != 'draft':
        messages.error(request, 'Можно редактировать только черновик')
        return redirect('frontend:invoice_detail', pk=pk)

    counterparties = Counterparty.objects.all()
    tasks = Task.objects.all()
    warehouse_items = WarehouseItem.objects.all()

    return render(request, 'frontend/invoice_form.html', {
        'invoice': invoice,
        'counterparties': counterparties,
        'tasks': tasks,
        'warehouse_items': warehouse_items,
    })


@login_required
def invoice_factura_list(request):
    facturas = InvoiceFactura.objects.all().select_related('counterparty', 'created_by')

    status_filter = request.GET.get('status', '')
    if status_filter:
        facturas = facturas.filter(status=status_filter)

    stats = {
        'total': facturas.count(),
        'draft': facturas.filter(status='draft').count(),
        'issued': facturas.filter(status='issued').count(),
    }

    from django.core.paginator import Paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(facturas, 20)
    facturas_page = paginator.get_page(page)

    return render(request, 'frontend/invoice_factura_list.html', {
        'facturas': facturas_page,
        'stats': stats,
        'current_filters': {'status': status_filter}
    })


@login_required
def invoice_factura_detail(request, pk):
    factura = get_object_or_404(InvoiceFactura.objects.select_related('counterparty', 'expense', 'completion_act',
                                                                      'created_by').prefetch_related('items'), pk=pk)
    return render(request, 'frontend/invoice_factura_detail.html', {'factura': factura})


@login_required
def invoice_factura_create(request):
    counterparties = Counterparty.objects.all()
    expenses = WarehouseExpense.objects.filter(status='conducted')
    acts = CompletionAct.objects.filter(status='signed')
    return render(request, 'frontend/invoice_factura_form.html', {
        'counterparties': counterparties,
        'expenses': expenses,
        'acts': acts,
    })


@login_required
def invoice_factura_edit(request, pk):
    factura = get_object_or_404(InvoiceFactura, pk=pk)
    if factura.status != 'draft':
        messages.error(request, 'Можно редактировать только черновик')
        return redirect('frontend:invoice_factura_detail', pk=pk)
    counterparties = Counterparty.objects.all()
    expenses = WarehouseExpense.objects.filter(status='conducted')
    acts = CompletionAct.objects.filter(status='signed')
    return render(request, 'frontend/invoice_factura_form.html', {
        'factura': factura,
        'counterparties': counterparties,
        'expenses': expenses,
        'acts': acts,
    })


# Для генерации PDF
def generate_pdf(request, model, pk, template_name, filename_prefix):
    """
    Универсальная функция для генерации PDF.

    model - класс модели (Invoice, InvoiceFactura, WarehouseReceipt и т.д.)
    pk - id объекта
    template_name - путь к шаблону ('documents/pdf/invoice_pdf.html')
    filename_prefix - префикс имени файла ('invoice', 'factura')
    """
    obj = get_object_or_404(model, pk=pk)

    # Определяем имя контекста по имени модели
    context_key = model.__name__.lower()
    context = {context_key: obj}

    html_string = render_to_string(template_name, context, request=request)
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    result = html.write_pdf()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename_prefix}_{obj.number}.pdf"'
    response.write(result)

    return response


@login_required
def invoice_pdf(request, pk):
    return generate_pdf(request, Invoice, pk, 'documents/pdf/invoice_pdf.html', 'invoice')


@login_required
def invoice_factura_pdf(request, pk):
    return generate_pdf(request, InvoiceFactura, pk, 'documents/pdf/invoice_factura_pdf.html', 'factura')


@login_required
def warehouse_receipt_pdf(request, pk):
    return generate_pdf(request, WarehouseReceipt, pk, 'documents/pdf/receipt_pdf.html', 'receipt')


@login_required
def warehouse_expense_pdf(request, pk):
    return generate_pdf(request, WarehouseExpense, pk, 'documents/pdf/expense_pdf.html', 'expense')


@login_required
def completion_act_pdf(request, pk):
    return generate_pdf(request, CompletionAct, pk, 'documents/pdf/act_pdf.html', 'act')


@login_required
def work_order_pdf(request, pk):
    return generate_pdf(request, WorkOrder, pk, 'documents/pdf/work_order_pdf.html', 'work_order')


@login_required
def manufacturer_list(request):
    manufacturers = Manufacturer.objects.all()
    return render(request, 'frontend/manufacturer_list.html', {'manufacturers': manufacturers})


@login_required
def manufacturer_create(request):
    if request.method == 'POST':
        # Через JS
        pass
    return render(request, 'frontend/manufacturer_form.html')


@login_required
def manufacturer_edit(request, pk):
    manufacturer = get_object_or_404(Manufacturer, pk=pk)
    return render(request, 'frontend/manufacturer_form.html', {'manufacturer': manufacturer})


@login_required
def warehouse_category_list(request):
    categories = Category.objects.all()
    return render(request, 'frontend/warehouse_category_list.html', {'categories': categories})


@login_required
def warehouse_category_create(request):
    categories = Category.objects.all()
    return render(request, 'frontend/warehouse_category_form.html', {'categories': categories})


@login_required
def warehouse_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    categories = Category.objects.exclude(pk=pk)
    return render(request, 'frontend/warehouse_category_form.html', {'category': category, 'categories': categories})


@login_required
def inventory_category_list(request):
    categories = InventoryCategory.objects.all()
    return render(request, 'frontend/inventory_category_list.html', {'categories': categories})


@login_required
def inventory_category_create(request):
    categories = InventoryCategory.objects.all()
    return render(request, 'frontend/inventory_category_form.html', {'categories': categories})


@login_required
def inventory_category_edit(request, pk):
    category = get_object_or_404(InventoryCategory, pk=pk)
    categories = InventoryCategory.objects.exclude(pk=pk)
    return render(request, 'frontend/inventory_category_form.html', {'category': category, 'categories': categories})


# ========== Стеллажи ==========
@login_required
def rack_list(request):
    """Список стеллажей по отделам"""
    racks = WarehouseRack.objects.all().select_related('department').prefetch_related('cells')

    department_filter = request.GET.get('department', '')
    if department_filter:
        racks = racks.filter(department_id=department_filter)

    departments = Department.objects.all()

    context = {
        'racks': racks,
        'departments': departments,
        'current_filters': {'department': department_filter}
    }
    return render(request, 'frontend/rack_list.html', context)


@login_required
def rack_detail(request, pk):
    """Детальная страница стеллажа с ячейками"""
    rack = get_object_or_404(WarehouseRack.objects.select_related('department').prefetch_related('cells', 'images'),
                             pk=pk)
    return render(request, 'frontend/rack_detail.html', {'rack': rack})


@login_required
def rack_create(request):
    departments = Department.objects.all()
    return render(request, 'frontend/rack_form.html', {'departments': departments})


@login_required
def rack_edit(request, pk):
    rack = get_object_or_404(WarehouseRack, pk=pk)
    departments = Department.objects.all()
    return render(request, 'frontend/rack_form.html', {'rack': rack, 'departments': departments})


# ========== Ячейки ==========
@login_required
def cell_list(request):
    cells = WarehouseCell.objects.all().select_related('rack', 'rack__department')
    return render(request, 'frontend/cell_list.html', {'cells': cells})


@login_required
def cell_detail(request, pk):
    cell = get_object_or_404(
        WarehouseCell.objects.select_related('rack', 'rack__department').prefetch_related('images', 'items'), pk=pk)
    return render(request, 'frontend/cell_detail.html', {'cell': cell})


@login_required
def cell_create(request):
    racks = WarehouseRack.objects.all().select_related('department')
    preselected_rack = request.GET.get('rack')
    return render(request, 'frontend/cell_form.html', {
        'racks': racks,
        'preselected_rack': int(preselected_rack) if preselected_rack else None
    })


@login_required
def cell_edit(request, pk):
    cell = get_object_or_404(WarehouseCell, pk=pk)
    racks = WarehouseRack.objects.all().select_related('department')
    return render(request, 'frontend/cell_form.html', {'cell': cell, 'racks': racks})


@login_required
def warehouse_transfer_pdf(request, pk):
    return generate_pdf(request, WarehouseTransfer, pk, 'documents/pdf/transfer_pdf.html', 'transfer')


@login_required
def warehouse_stocktake_pdf(request, pk):
    return generate_pdf(request, WarehouseStocktake, pk, 'documents/pdf/stocktake_pdf.html', 'stocktake')


@login_required
def warehouse_stock_report(request):
    """Отчёт по остаткам на складах"""
    user = request.user

    # Определяем доступные склады
    if user.is_staff or user.is_superuser:
        departments = Department.objects.all()
    else:
        departments = Department.objects.filter(id=user.department_id) if user.department else Department.objects.none()

    # Фильтры
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')

    # Получаем все товары с выбранных складов
    items = WarehouseItem.objects.all().select_related('category', 'department')

    if category_filter:
        items = items.filter(category_id=category_filter)
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(article__icontains=search_query)
        )

    # Группируем по товару (название + артикул)
    from collections import defaultdict
    stock_data = defaultdict(lambda: {'total': 0, 'by_dept': {}})

    for item in items:
        key = f"{item.name}|{item.article or ''}"
        stock_data[key]['name'] = item.name
        stock_data[key]['article'] = item.article
        stock_data[key]['category'] = item.category.name if item.category else '—'
        stock_data[key]['unit'] = item.get_unit_display()
        stock_data[key]['total'] += item.quantity
        stock_data[key]['by_dept'][item.department_id] = item.quantity

    # Преобразуем в список для шаблона
    report_data = []
    for key, data in stock_data.items():
        row = {
            'name': data['name'],
            'article': data['article'],
            'category': data['category'],
            'unit': data['unit'],
            'total': data['total'],
            'quantities': []
        }
        for dept in departments:
            row['quantities'].append(data['by_dept'].get(dept.id, 0))
        report_data.append(row)

    # Сортировка
    report_data.sort(key=lambda x: x['name'])

    # Категории для фильтра
    categories = Category.objects.all()

    context = {
        'report_data': report_data,
        'departments': departments,
        'categories': categories,
        'current_filters': {
            'category': category_filter,
            'search': search_query,
        }
    }

    return render(request, 'frontend/warehouse_stock_report.html', context)


@login_required
def warehouse_turnover_report(request):
    """Оборотная ведомость по складу"""
    user = request.user

    # Определяем доступные склады
    if user.is_staff or user.is_superuser:
        departments = Department.objects.all()
    else:
        departments = Department.objects.filter(id=user.department_id) if user.department else Department.objects.none()

    # Фильтры
    department_filter = request.GET.get('department', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # По умолчанию — текущий месяц
    today = timezone.now().date()
    if not date_from:
        date_from = today.replace(day=1).strftime('%Y-%m-%d')
    if not date_to:
        # Последний день месяца
        next_month = today.replace(day=28) + timezone.timedelta(days=4)
        date_to = (next_month - timezone.timedelta(days=next_month.day)).strftime('%Y-%m-%d')

    # Получаем транзакции
    from warehouse.models import WarehouseTransaction
    transactions = WarehouseTransaction.objects.select_related(
        'item', 'item__category', 'from_department', 'to_department'
    ).filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )

    if department_filter:
        transactions = transactions.filter(
            Q(from_department_id=department_filter) | Q(to_department_id=department_filter)
        )

    # Группируем по товару
    from collections import defaultdict
    turnover_data = defaultdict(lambda: {
        'name': '', 'article': '', 'category': '', 'unit': '',
        'in': 0, 'out': 0, 'start_balance': 0, 'end_balance': 0
    })

    for t in transactions:
        item = t.item
        key = item.id

        turnover_data[key]['name'] = item.name
        turnover_data[key]['article'] = item.article or ''
        turnover_data[key]['category'] = item.category.name if item.category else '—'
        turnover_data[key]['unit'] = item.get_unit_display()

        if t.transaction_type == 'in':
            turnover_data[key]['in'] += t.quantity
        elif t.transaction_type == 'out':
            turnover_data[key]['out'] += t.quantity
        elif t.transaction_type == 'move':
            # Для перемещения: списание с отправителя, приход получателю
            if t.from_department_id and str(t.from_department_id) == department_filter:
                turnover_data[key]['out'] += t.quantity
            if t.to_department_id and str(t.to_department_id) == department_filter:
                turnover_data[key]['in'] += t.quantity

    # Считаем начальные и конечные остатки
    from django.db.models import Sum
    for key, data in turnover_data.items():
        # Начальный остаток = текущий - приход + расход
        current_qty = WarehouseItem.objects.get(id=key).quantity
        data['end_balance'] = current_qty
        data['start_balance'] = current_qty - data['in'] + data['out']

    report_data = list(turnover_data.values())
    report_data.sort(key=lambda x: x['name'])

    context = {
        'report_data': report_data,
        'departments': departments,
        'current_filters': {
            'department': department_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
    }

    return render(request, 'frontend/warehouse_turnover_report.html', context)


@login_required
def warehouse_stock_report_pdf(request):
    """PDF отчёта по остаткам"""
    user = request.user

    if user.is_staff or user.is_superuser:
        departments = Department.objects.all()
    else:
        departments = Department.objects.filter(id=user.department_id) if user.department else Department.objects.none()

    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')

    items = WarehouseItem.objects.all().select_related('category', 'department')

    if category_filter:
        items = items.filter(category_id=category_filter)
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(article__icontains=search_query)
        )

    from collections import defaultdict
    stock_data = defaultdict(lambda: {'total': 0, 'by_dept': {}})

    for item in items:
        key = f"{item.name}|{item.article or ''}"
        stock_data[key]['name'] = item.name
        stock_data[key]['article'] = item.article
        stock_data[key]['category'] = item.category.name if item.category else '—'
        stock_data[key]['unit'] = item.get_unit_display()
        stock_data[key]['total'] += item.quantity
        stock_data[key]['by_dept'][item.department_id] = item.quantity

    report_data = []
    for key, data in stock_data.items():
        row = {
            'name': data['name'],
            'article': data['article'],
            'category': data['category'],
            'unit': data['unit'],
            'total': data['total'],
            'quantities': []
        }
        for dept in departments:
            row['quantities'].append(data['by_dept'].get(dept.id, 0))
        report_data.append(row)

    report_data.sort(key=lambda x: x['name'])

    html_string = render_to_string('documents/pdf/stock_report_pdf.html', {
        'report_data': report_data,
        'departments': departments,
        'date': timezone.now().date(),
    }, request=request)

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    result = html.write_pdf()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="stock_report.pdf"'
    response.write(result)

    return response


@login_required
def warehouse_turnover_report_pdf(request):
    """PDF оборотной ведомости"""
    user = request.user

    if user.is_staff or user.is_superuser:
        departments = Department.objects.all()
    else:
        departments = Department.objects.filter(id=user.department_id) if user.department else Department.objects.none()

    department_filter = request.GET.get('department', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    today = timezone.now().date()
    if not date_from:
        date_from = today.replace(day=1).strftime('%Y-%m-%d')
    if not date_to:
        next_month = today.replace(day=28) + timezone.timedelta(days=4)
        date_to = (next_month - timezone.timedelta(days=next_month.day)).strftime('%Y-%m-%d')

    from warehouse.models import WarehouseTransaction
    transactions = WarehouseTransaction.objects.select_related(
        'item', 'item__category', 'from_department', 'to_department'
    ).filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )

    if department_filter:
        transactions = transactions.filter(
            Q(from_department_id=department_filter) | Q(to_department_id=department_filter)
        )

    from collections import defaultdict
    turnover_data = defaultdict(lambda: {
        'name': '', 'article': '', 'category': '', 'unit': '',
        'in': 0, 'out': 0, 'start_balance': 0, 'end_balance': 0
    })

    for t in transactions:
        item = t.item
        key = item.id

        turnover_data[key]['name'] = item.name
        turnover_data[key]['article'] = item.article or ''
        turnover_data[key]['category'] = item.category.name if item.category else '—'
        turnover_data[key]['unit'] = item.get_unit_display()

        if t.transaction_type == 'in':
            turnover_data[key]['in'] += t.quantity
        elif t.transaction_type == 'out':
            turnover_data[key]['out'] += t.quantity
        elif t.transaction_type == 'move':
            if t.from_department_id and str(t.from_department_id) == department_filter:
                turnover_data[key]['out'] += t.quantity
            if t.to_department_id and str(t.to_department_id) == department_filter:
                turnover_data[key]['in'] += t.quantity

    for key, data in turnover_data.items():
        current_qty = WarehouseItem.objects.get(id=key).quantity
        data['end_balance'] = current_qty
        data['start_balance'] = current_qty - data['in'] + data['out']

    report_data = list(turnover_data.values())
    report_data.sort(key=lambda x: x['name'])

    html_string = render_to_string('documents/pdf/turnover_report_pdf.html', {
        'report_data': report_data,
        'date_from': date_from,
        'date_to': date_to,
        'department': departments.filter(id=department_filter).first() if department_filter else None,
    }, request=request)

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    result = html.write_pdf()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="turnover_report.pdf"'
    response.write(result)

    return response
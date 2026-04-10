from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q, F
from django.db.models import Sum
from django.contrib import messages

from tasks.models import Task
from tasks.serializers import TaskListSerializer
from counterparties.models import Counterparty
from warehouse.models import WarehouseItem
from inventory.models import InventoryItem
from documents.models import MaterialRequest, InventoryIssue
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def dashboard(request):
    user = request.user
    today = timezone.now().date()

    # Мои задачи
    my_tasks = Task.objects.filter(
        Q(responsible=user) | Q(co_executors=user)
    ).exclude(status__in=['completed', 'closed', 'cancelled']).distinct()

    my_tasks_count = my_tasks.count()
    overdue_tasks = my_tasks.filter(deadline__lt=today).count()

    # Товары с низким остатком
    low_stock = WarehouseItem.objects.filter(quantity__lte=F('min_stock')).count()
    warehouse_items = WarehouseItem.objects.count()

    # Инвентарь
    active_inventory = InventoryItem.objects.filter(status='active', responsible__isnull=False).count()
    available_inventory = InventoryItem.objects.filter(status='active', responsible__isnull=True).count()

    # Документы
    pending_docs = MaterialRequest.objects.filter(status__in=['pending', 'approved']).count() + \
                   InventoryIssue.objects.filter(status__in=['pending', 'approved']).count()

    # Последние задачи
    recent_tasks = my_tasks.order_by('-created_at')[:5]

    context = {
        'today': today,
        'my_tasks_count': my_tasks_count,
        'overdue_tasks': overdue_tasks,
        'warehouse_items': warehouse_items,
        'low_stock': low_stock,
        'active_inventory': active_inventory,
        'available_inventory': available_inventory,
        'pending_docs': pending_docs,
        'recent_tasks': recent_tasks,
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

    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if my_only == 'true':
        tasks = tasks.filter(responsible=user)
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
    """Список складских позиций"""
    items = WarehouseItem.objects.all().select_related(
        'category', 'manufacturer', 'department'
    )

    # Фильтры
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

    # Статистика
    stats = {
        'total': items.count(),
        'total_quantity': items.aggregate(sum=Sum('quantity'))['sum'] or 0,
        'low_stock': items.filter(quantity__lte=F('min_stock')).count(),
        'categories': items.values('category').distinct().count(),
    }

    # Категории и производители для фильтров
    from categories.models import Category
    from manufacturers.models import Manufacturer
    categories = Category.objects.all()
    manufacturers = Manufacturer.objects.all()

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
        'current_filters': {
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

    context = {
        'categories': Category.objects.all(),
        'manufacturers': Manufacturer.objects.all(),
        'departments': Department.objects.all(),
        'unit_choices': WarehouseItem.UNIT_CHOICES,
    }

    return render(request, 'frontend/warehouse_form.html', context)


@login_required
def warehouse_edit(request, pk):
    """Редактирование складской позиции"""
    item = get_object_or_404(WarehouseItem, pk=pk)

    from categories.models import Category
    from manufacturers.models import Manufacturer
    from departments.models import Department

    context = {
        'item': item,
        'categories': Category.objects.all(),
        'manufacturers': Manufacturer.objects.all(),
        'departments': Department.objects.all(),
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


# Остальные заглушки

@login_required
def material_requests_list(request):
    return render(request, 'frontend/stub.html', {'title': 'Документы'})


@login_required
def chat_index(request):
    return render(request, 'frontend/stub.html', {'title': 'Чат'})


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

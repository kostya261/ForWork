from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import MaterialRequestViewSet, InventoryIssueViewSet, WarehouseExpenseViewSet, WarehouseTransferViewSet, \
    WarehouseStocktakeViewSet, InventoryWriteOffViewSet, InventoryTransferViewSet, InventoryStocktakeViewSet, \
    WorkOrderViewSet, CompletionActViewSet, InvoiceViewSet, InvoiceFacturaViewSet
from .views import WarehouseReceiptViewSet

router = DefaultRouter()
router.register(r'material-requests', MaterialRequestViewSet, basename='material-request')
router.register(r'inventory-issues', InventoryIssueViewSet, basename='inventory-issue')
router.register(r'receipts', WarehouseReceiptViewSet, basename='receipt')
router.register(r'expenses', WarehouseExpenseViewSet, basename='expense')
router.register(r'transfers', WarehouseTransferViewSet, basename='transfer')
router.register(r'stocktakes', WarehouseStocktakeViewSet, basename='stocktake')
router.register(r'inventory-writeoffs', InventoryWriteOffViewSet, basename='inventory-writeoff')
router.register(r'inventory-transfers', InventoryTransferViewSet, basename='inventory-transfer')
router.register(r'inventory-stocktakes', InventoryStocktakeViewSet, basename='inventory-stocktake')
router.register(r'work-orders', WorkOrderViewSet, basename='work-order')
router.register(r'completion-acts', CompletionActViewSet, basename='completion-act')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'invoice-facturas', InvoiceFacturaViewSet, basename='invoice-factura')


urlpatterns = [
    path('documents/', include(router.urls)),
]
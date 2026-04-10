from rest_framework.routers import DefaultRouter
from .views import CounterpartyViewSet, CounterpartyBankAccountViewSet

router = DefaultRouter()
router.register(r'counterparties', CounterpartyViewSet, basename='counterparty')
router.register(r'bank-accounts', CounterpartyBankAccountViewSet, basename='bank-account')

urlpatterns = router.urls
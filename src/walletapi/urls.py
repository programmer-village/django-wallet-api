from django.urls import path
from .views import WalletDetail, WalletListCreate, perform_operation  # Добавлен импорт функции perform_operation

urlpatterns = [
    path('api/v1/wallets/', WalletListCreate.as_view(), name='wallet_list_create'),
    path('api/v1/wallets/<uuid:uuid>/', WalletDetail.as_view(), name='wallet_detail'),
    path('api/v1/wallets/<uuid:wallet_uuid>/operation/', perform_operation, name='perform_operation'),  # Добавлен маршрут для операции
]
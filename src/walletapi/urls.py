from django.urls import path
from .views import WalletDetail, perform_operation, \
    WalletListCreate  # Предположим, у вас есть вьюха для создания кошелька

urlpatterns = [
    path('api/v1/wallets/', WalletListCreate.as_view(), name='wallet_list_create'),
    path('api/v1/wallets/<uuid:uuid>/', WalletDetail.as_view(), name='wallet_detail'),
    path('api/v1/wallets/<uuid:wallet_uuid>/operation/', perform_operation, name='perform_operation'),
]

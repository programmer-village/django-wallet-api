import pytest
from rest_framework import status
from rest_framework.test import APIClient
from .models import Wallet
from django.contrib.auth.models import User
from decimal import Decimal
import uuid


import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'wallet.settings'
django.setup()


@pytest.mark.django_db
class TestWalletEndpoints:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('100.00'), uuid=uuid.uuid4())

    def test_create_wallet(self):
        response = self.client.post('/api/v1/wallets/', {'balance': '50.00'})
        assert response.status_code == status.HTTP_201_CREATED
        assert Wallet.objects.count() == 2  # Проверка создания нового кошелька
        assert Wallet.objects.last().balance == Decimal('50.00')

    def test_list_wallets(self):
        response = self.client.get('/api/v1/wallets/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # Должен вернуть только кошелек текущего пользователя

    def test_wallet_detail(self):
        response = self.client.get(f'/api/v1/wallets/{self.wallet.uuid}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['balance'] == str(self.wallet.balance)

    def test_wallet_detail_permission_denied(self):
        another_user = User.objects.create_user(username='anotheruser', password='anotherpass')
        self.client.force_authenticate(user=another_user)
        response = self.client.get(f'/api/v1/wallets/{self.wallet.uuid}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_perform_deposit(self):
        response = self.client.post(f'/api/v1/wallets/{self.wallet.uuid}/operation/', {
            'operationType': 'DEPOSIT',
            'amount': '50.00'
        })
        assert response.status_code == status.HTTP_200_OK
        self.wallet.refresh_from_db()
        assert self.wallet.balance == Decimal('150.00')

    def test_perform_withdraw(self):
        response = self.client.post(f'/api/v1/wallets/{self.wallet.uuid}/operation/', {
            'operationType': 'WITHDRAW',
            'amount': '30.00'
        })
        assert response.status_code == status.HTTP_200_OK
        self.wallet.refresh_from_db()
        assert self.wallet.balance == Decimal('70.00')

    def test_perform_withdraw_insufficient_funds(self):
        response = self.client.post(f'/api/v1/wallets/{self.wallet.uuid}/operation/', {
            'operationType': 'WITHDRAW',
            'amount': '200.00'  # Запрос на вывод больше чем баланс
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        self.wallet.refresh_from_db()
        assert self.wallet.balance == Decimal('100.00')  # Баланс не изменился

    def test_perform_operation_invalid_type(self):
        response = self.client.post(f'/api/v1/wallets/{self.wallet.uuid}/operation/', {
            'operationType': 'INVALID_OPERATION',
            'amount': '50.00'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_perform_operation_invalid_amount(self):
        response = self.client.post(f'/api/v1/wallets/{self.wallet.uuid}/operation/', {
            'operationType': 'DEPOSIT',
            'amount': '-50.00'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
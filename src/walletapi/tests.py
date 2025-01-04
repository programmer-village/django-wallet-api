import os

from wallet import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wallet.settings")

from django.apps import apps

apps.populate(settings.INSTALLED_APPS)

import os

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import Wallet
from decimal import Decimal
from rest_framework.authtoken.models import Token


class WalletAPITestCase(APITestCase):
    def setUp(self):
        # Создаем пользователей
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.other_user = User.objects.create_user(username='otheruser', password='password456')

        # Генерируем токен для пользователя
        self.token = Token.objects.create(user=self.user)

        # Инициализируем клиента
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Создаем тестовые кошельки
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal("1000.00"))
        self.other_wallet = Wallet.objects.create(user=self.other_user, balance=Decimal("500.00"))

        # URLs для тестов
        self.wallet_list_url = '/api/v1/wallets/'  # Получение списка кошельков
        self.operation_url = f'/api/v1/wallets/{self.wallet.uuid}/operation/'

    def test_list_wallets(self):
        """Тест: Получение списка кошельков текущего авторизованного пользователя."""
        response = self.client.get(self.wallet_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Только один кошелёк принадлежит self.user

    def test_create_wallet(self):
        """Тест: Создание нового кошелька."""
        data = {"balance": "500.00"}
        response = self.client.post(self.wallet_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Wallet.objects.filter(user=self.user).count(), 2)  # Теперь два кошелька

    def test_perform_deposit(self):
        """Тест: Успешное пополнение баланса кошелька."""
        data = {"operationType": "DEPOSIT", "amount": "200.00"}
        response = self.client.post(self.operation_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("1200.00"))  # 1000 + 200

    def test_perform_withdraw(self):
        """Тест: Успешное снятие средств с кошелька."""
        data = {"operationType": "WITHDRAW", "amount": "300.00"}
        response = self.client.post(self.operation_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("700.00"))  # 1000 - 300

    def test_withdraw_insufficient_funds(self):
        """Тест: Ошибка при снятии суммы больше баланса."""
        data = {"operationType": "WITHDRAW", "amount": "1500.00"}
        response = self.client.post(self.operation_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("1000.00"))  # Баланс не изменён

    def test_access_other_user_wallet(self):
        """Тест: Попытка выполнить операцию с чужим кошельком."""
        other_wallet_operation_url = f'/api/v1/wallets/{self.other_wallet.uuid}/operation/'
        data = {"operationType": "DEPOSIT", "amount": "100.00"}
        response = self.client.post(other_wallet_operation_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_access(self):
        """Тест: Запрос без аутентификации."""
        self.client.credentials()  # Сбрасываем заголовки аутентификации
        response = self.client.get(self.wallet_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

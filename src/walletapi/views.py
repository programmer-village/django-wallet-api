from .constants import ERROR_MESSAGES
from .models import Wallet, OperationType
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .serializers import WalletSerializer
from decimal import Decimal


class WalletListCreate(generics.ListCreateAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WalletDetail(generics.RetrieveAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'

    def get(self, request, *args, **kwargs):
        wallet = self.get_object()
        if wallet.user != request.user:
            return Response({'error': 'You do not have permission to access this wallet'},
                            status=status.HTTP_403_FORBIDDEN)
        return Response(self.serializer_class(wallet).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def perform_operation(request, wallet_uuid):
    """
    Обрабатывает операцию над кошельком (DEPOSIT или WITHDRAW).
    :param request: HTTP запрос.
    :param wallet_uuid: UUID кошелька.
    """
    try:
        with transaction.atomic():
            # Попытка получить кошелек с блокировкой на уровне записи в БД
            wallet = Wallet.objects.select_for_update().get(uuid=wallet_uuid)
            if wallet.user != request.user:
                return Response({'error': ERROR_MESSAGES["permission_denied"]},
                                status=status.HTTP_403_FORBIDDEN)

            # Извлечение данных из тела запроса
            operation_type = request.data.get('operationType')  # ключ 'operationType' — обязательный
            amount = request.data.get('amount')  # ключ 'amount' — обязательный

            # Проверка operationType
            if operation_type not in [OperationType.DEPOSIT, OperationType.WITHDRAW]:
                return Response({'error': ERROR_MESSAGES["invalid_operation"]},
                                status=status.HTTP_400_BAD_REQUEST)

            # Проверка, что amount передан корректно (является положительным числом)
            try:
                amount = Decimal(amount)
                if amount < 0:
                    raise ValueError()
            except (ValueError, TypeError):
                return Response({'error': ERROR_MESSAGES["invalid_amount"]},
                                status=status.HTTP_400_BAD_REQUEST)

            # Выполнение операции
            if operation_type == OperationType.DEPOSIT:
                wallet.balance += amount

            elif operation_type == OperationType.WITHDRAW:
                if wallet.balance < amount:
                    return Response({'error': ERROR_MESSAGES["insufficient_funds"]},
                                    status=status.HTTP_400_BAD_REQUEST)
                wallet.balance -= amount
                wallet.save()
            wallet.save()

            # Формируем успешный ответ с обновленным балансом
            return Response({
                'operation_type': operation_type,
                'amount': str(amount),
                'balance': str(wallet.balance)
            }, status=status.HTTP_200_OK)

    except Wallet.DoesNotExist:
        return Response({'error': ERROR_MESSAGES["wallet_not_found"]}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Унифицированная обработка любых других возможных ошибок
        return Response({'error': f'An unexpected error occurred: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

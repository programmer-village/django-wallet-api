from .models import Wallet, OperationType
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from rest_framework.exceptions import ParseError
from django.db import IntegrityError
from .serializers import WalletSerializer


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
    try:
        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(uuid=wallet_uuid)
            if wallet.user != request.user:
                return Response({'error': 'You do not have permission to perform operations on this wallet'},
                                status=status.HTTP_403_FORBIDDEN)

            operation_type = request.data.get('operationType')
            amount = request.data.get('amount')

            if operation_type not in [OperationType.DEPOSIT, OperationType.WITHDRAW]:
                return Response({'error': 'Invalid operation type'}, status=status.HTTP_400_BAD_REQUEST)
            if amount <= 0:
                return Response({'error': 'Amount must be greater than zero'}, status=status.HTTP_400_BAD_REQUEST)

            if operation_type == OperationType.DEPOSIT:
                wallet.deposit(amount)
            elif operation_type == OperationType.WITHDRAW:
                wallet.withdraw(amount)

            return Response({'balance': str(wallet.balance)}, status=status.HTTP_200_OK)

    except Wallet.DoesNotExist:
        return Response({'error': 'Wallet not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except ParseError:
        return Response({'error': 'Invalid JSON format'}, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError:
        return Response({'error': 'Database integrity error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

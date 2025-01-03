from .models import Wallet
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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

from django.contrib import admin
from .models import Wallet

from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'user', 'balance', 'created_at', 'updated_at')
    search_fields = ('user__username',)
    ordering = ('-created_at',)  # Сортировка по дате создания в обратном порядке.
    list_filter = ('created_at',)  # Фильтрация по дате создания кошелька.



from django.db import models
import uuid

from django.core.exceptions import ValidationError


def validate_balance(value):
    if value < 0:
        raise ValidationError('Баланс не может быть отрицательным.')


class Wallet(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[validate_balance])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet {self.uuid} - Balance: {self.balance}"

    def deposit(self, amount):
        self.balance += amount
        self.save()

    def withdraw(self, amount):
        if self.balance < amount:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        self.save()


# Определение типов операций (можно использовать Enum)
class OperationType(models.TextChoices):
    DEPOSIT = 'DEPOSIT', 'Deposit'
    WITHDRAW = 'WITHDRAW', 'Withdraw'
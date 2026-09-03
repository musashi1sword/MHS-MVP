from rest_framework import serializers

from .models import Transaction, Wallet


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ("balance", "currency")


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            "id",
            "user",
            "kind",
            "provider",
            "amount",
            "currency",
            "status",
            "reference",
            "appointment",
            "metadata",
            "created_at",
        )
        read_only_fields = ("user", "status", "reference", "created_at")


class ChargeSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=[c[0] for c in Transaction.TYPES], default="consult_fee")
    provider = serializers.ChoiceField(choices=["mpesa", "airtel", "stripe"])
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(default="KES")
    phone = serializers.CharField(required=False, allow_blank=True)
    appointment = serializers.IntegerField(required=False)


class PayoutSerializer(serializers.Serializer):
    provider_user = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(default="USD")
    destination = serializers.CharField(help_text="IBAN / account reference for the IC wire.")

from rest_framework import serializers

from apps.wallet.constants import NETWORK_CHOICES, SUPPORTED_NETWORKS


class WithdrawSerializer(serializers.Serializer):
    amount_usd = serializers.DecimalField(max_digits=12, decimal_places=2)
    usdt_address = serializers.CharField(max_length=128)
    network = serializers.ChoiceField(choices=NETWORK_CHOICES)

    def validate_network(self, value):
        if value not in SUPPORTED_NETWORKS:
            raise serializers.ValidationError("Неподдерживаемая сеть")
        return value


class SaveAddressSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=128)
    network = serializers.ChoiceField(choices=NETWORK_CHOICES)

    def validate_network(self, value):
        if value not in SUPPORTED_NETWORKS:
            raise serializers.ValidationError("Неподдерживаемая сеть")
        return value

    def validate_address(self, value):
        address = value.strip()
        if not address:
            raise serializers.ValidationError("Адрес не может быть пустым")
        return address

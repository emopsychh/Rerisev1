from rest_framework import serializers

from apps.commerce.models import Order


class CreateOrderSerializer(serializers.Serializer):
    product_id = serializers.CharField(max_length=50)
    order_type = serializers.ChoiceField(
        choices=[choice[0] for choice in Order.ORDER_TYPE_CHOICES]
    )

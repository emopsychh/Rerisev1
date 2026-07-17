from rest_framework import serializers

from apps.crm.constants import STAGE_SLUGS


class LeadCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    source = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    contact = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    stage = serializers.ChoiceField(choices=STAGE_SLUGS, required=False, default="new")
    task = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    value_usd = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)


class LeadUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=255)
    source = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    contact = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=100)
    stage = serializers.ChoiceField(choices=STAGE_SLUGS, required=False)
    task = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    value_usd = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)

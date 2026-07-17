from rest_framework import serializers


class StartSessionSerializer(serializers.Serializer):
    scenario_id = serializers.IntegerField(required=False, allow_null=True)
    model = serializers.CharField(required=False, allow_blank=True, max_length=50)
    message = serializers.CharField(max_length=8000)


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=8000)

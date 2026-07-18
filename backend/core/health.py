from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return JsonResponse({"status": "ok"})

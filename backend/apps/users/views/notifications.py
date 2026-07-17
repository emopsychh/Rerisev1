from rest_framework import generics, status
from rest_framework.views import APIView

from apps.users.models import Notification
from apps.users.selectors import count_unread_notifications
from apps.users.serializers import NotificationSerializer, NotificationSettingsSerializer
from core.pagination import StandardPagination
from core.responses import error_response, success_response


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        if self.request.query_params.get("unread_only", "").lower() == "true":
            queryset = queryset.filter(is_read=False)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        response.data["meta"]["unread"] = count_unread_notifications(request.user)
        return response


class NotificationReadView(APIView):
    def patch(self, request, pk):
        updated = Notification.objects.filter(
            user=request.user,
            pk=pk,
        ).update(is_read=True)

        if not updated:
            return error_response(
                "NOT_FOUND",
                "Уведомление не найдено",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return success_response({"is_read": True})


class NotificationReadAllView(APIView):
    def patch(self, request):
        marked = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).update(is_read=True)
        return success_response({"marked": marked})


class NotificationSettingsView(APIView):
    def patch(self, request):
        serializer = NotificationSettingsSerializer(
            instance=request.user.notification_settings,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data)

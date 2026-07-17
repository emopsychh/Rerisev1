from django.urls import path

from apps.admin_ops.views import (
    AdminAdjustmentView,
    AdminAuditLogView,
    AdminBlockUserView,
    AdminWithdrawalView,
)

urlpatterns = [
    path("admin/ledger/adjustments", AdminAdjustmentView.as_view(), name="admin-adjustments"),
    path("admin/users/<int:user_id>/block", AdminBlockUserView.as_view(), name="admin-block-user"),
    path(
        "admin/withdrawals/<int:withdrawal_id>",
        AdminWithdrawalView.as_view(),
        name="admin-withdrawal",
    ),
    path("admin/audit-log", AdminAuditLogView.as_view(), name="admin-audit-log"),
]

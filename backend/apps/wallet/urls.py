from django.urls import path

from apps.wallet.views.wallet import (
    WalletAddressView,
    WalletOverviewView,
    WalletTransactionsView,
    WalletWithdrawView,
)

urlpatterns = [
    path("wallet", WalletOverviewView.as_view(), name="wallet-overview"),
    path("wallet/transactions", WalletTransactionsView.as_view(), name="wallet-transactions"),
    path("wallet/withdraw", WalletWithdrawView.as_view(), name="wallet-withdraw"),
    path("wallet/address", WalletAddressView.as_view(), name="wallet-address"),
]

from django.conf import settings

from apps.commerce.providers.base import PaymentProviderError
from apps.commerce.providers.cryptobot import CryptoBotProvider
from apps.commerce.providers.manual import ManualCryptoProvider
from apps.commerce.providers.mock import MockCryptoProvider


def get_payment_provider():
    provider_name = settings.PAYMENT_PROVIDER
    if provider_name == "mock" and not settings.DEBUG:
        raise PaymentProviderError(
            "PAYMENT_PROVIDER=mock запрещён при DEBUG=false. "
            "Используйте manual или cryptobot."
        )
    if provider_name == "manual":
        return ManualCryptoProvider()
    if provider_name == "mock":
        return MockCryptoProvider()
    if provider_name == "cryptobot":
        return CryptoBotProvider()
    raise PaymentProviderError(f"Unsupported payment provider: {provider_name}")

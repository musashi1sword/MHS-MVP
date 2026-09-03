"""Payment gateway adapters. Each returns a normalised result dict:

    {"status": "success"|"failed"|"pending", "reference": "...", "raw": {...}}

In `mock` mode (the MVP default) they synthesise a plausible success without
touching the network, so the investor demo never depends on a live gateway.
"""
from __future__ import annotations

import secrets

from django.conf import settings


def _ref(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(6).upper()}"


class MpesaDarajaAdapter:
    provider = "mpesa"

    def charge(self, *, phone: str, amount, currency="KES", account_ref="MHS", **_) -> dict:
        if settings.MPESA_ENV == "mock":
            return {"status": "success", "reference": _ref("MPESA"), "raw": {"mode": "mock", "phone": phone}}
        # Live: STK push via Daraja would go here.
        raise NotImplementedError("Live M-Pesa Daraja integration not configured.")


class AirtelMoneyAdapter:
    provider = "airtel"

    def charge(self, *, phone: str, amount, currency="KES", **_) -> dict:
        if settings.AIRTEL_MONEY_ENV == "mock":
            return {"status": "success", "reference": _ref("AIRTEL"), "raw": {"mode": "mock", "phone": phone}}
        raise NotImplementedError("Live Airtel Money integration not configured.")


class StripeAdapter:
    """Used for overseas Independent Contractor payouts (international wire / transfer)."""

    provider = "stripe"

    def payout(self, *, destination: str, amount, currency="USD", **_) -> dict:
        if not settings.STRIPE_SECRET_KEY:
            return {"status": "success", "reference": _ref("PO"), "raw": {"mode": "mock", "destination": destination}}
        raise NotImplementedError("Live Stripe payout integration not configured.")

    def charge(self, *, amount, currency="USD", **_) -> dict:
        if not settings.STRIPE_SECRET_KEY:
            return {"status": "success", "reference": _ref("PI"), "raw": {"mode": "mock"}}
        raise NotImplementedError("Live Stripe integration not configured.")


ADAPTERS = {
    "mpesa": MpesaDarajaAdapter,
    "airtel": AirtelMoneyAdapter,
    "stripe": StripeAdapter,
}


def get_adapter(provider: str):
    try:
        return ADAPTERS[provider]()
    except KeyError:
        raise ValueError(f"Unknown payment provider '{provider}'.")

from typing import Any

import stripe
from sqlmodel import Session, select

from app.config import (
    STRIPE_CANCEL_URL,
    STRIPE_PRICE_ID_DESK,
    STRIPE_PRICE_ID_PRO,
    STRIPE_SECRET_KEY,
    STRIPE_SUCCESS_URL,
    STRIPE_WEBHOOK_SECRET,
)
from app.schemas import User
from app.services.auth import mark_tier_selection_complete, update_user_tier
from app.services.db import get_engine


def _require_stripe_config() -> None:
    if not STRIPE_SECRET_KEY:
        raise ValueError("Stripe is not configured (missing STRIPE_SECRET_KEY).")
    stripe.api_key = STRIPE_SECRET_KEY


def _price_id_for_tier(tier: str) -> str:
    if tier == "pro":
        if not STRIPE_PRICE_ID_PRO:
            raise ValueError("Missing STRIPE_PRICE_ID_PRO.")
        return STRIPE_PRICE_ID_PRO
    if tier == "desk":
        if not STRIPE_PRICE_ID_DESK:
            raise ValueError("Missing STRIPE_PRICE_ID_DESK.")
        return STRIPE_PRICE_ID_DESK
    raise ValueError("Unsupported checkout tier.")


def _tier_for_price_id(price_id: str | None) -> str | None:
    if not price_id:
        return None
    if STRIPE_PRICE_ID_DESK and price_id == STRIPE_PRICE_ID_DESK:
        return "desk"
    if STRIPE_PRICE_ID_PRO and price_id == STRIPE_PRICE_ID_PRO:
        return "pro"
    return None


def _extract_subscription_tier(subscription: dict[str, Any]) -> str | None:
    items = ((subscription.get("items") or {}).get("data") or [])
    for item in items:
        price = item.get("price") or {}
        tier = _tier_for_price_id(price.get("id"))
        if tier:
            return tier
    return None


def _set_user_stripe_fields(user_id: int, customer_id: str | None, subscription_id: str | None) -> None:
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if not user:
            return
        if customer_id:
            user.stripe_customer_id = customer_id
        if subscription_id is not None:
            user.stripe_subscription_id = subscription_id
        session.add(user)
        session.commit()


def _resolve_user_id_for_customer(customer_id: str | None) -> int | None:
    if not customer_id:
        return None
    with Session(get_engine()) as session:
        user = session.exec(select(User).where(User.stripe_customer_id == customer_id)).first()
        return user.id if user else None


def _get_or_create_customer(user: User) -> str:
    if user.stripe_customer_id:
        return user.stripe_customer_id
    customer = stripe.Customer.create(
        email=user.email,
        name=user.name,
        metadata={"user_id": str(user.id)},
    )
    return customer["id"]


def create_checkout_session(user_id: int, tier: str) -> str:
    _require_stripe_config()
    price_id = _price_id_for_tier(tier)

    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
        customer_id = _get_or_create_customer(user)
        user.stripe_customer_id = customer_id
        session.add(user)
        session.commit()

    checkout = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=STRIPE_SUCCESS_URL,
        cancel_url=STRIPE_CANCEL_URL,
        allow_promotion_codes=True,
        metadata={"user_id": str(user_id), "tier": tier},
        subscription_data={"metadata": {"user_id": str(user_id), "tier": tier}},
    )
    return checkout["url"]


def create_customer_portal_session(user_id: int) -> str:
    _require_stripe_config()
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
        customer_id = _get_or_create_customer(user)
        user.stripe_customer_id = customer_id
        session.add(user)
        session.commit()

    portal = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=STRIPE_SUCCESS_URL,
    )
    return portal["url"]


def create_subscription_payment_intent(user_id: int, tier: str) -> dict[str, str]:
    _require_stripe_config()
    price_id = _price_id_for_tier(tier)

    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
        customer_id = _get_or_create_customer(user)
        user.stripe_customer_id = customer_id
        session.add(user)
        session.commit()

    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id}],
        payment_behavior="default_incomplete",
        payment_settings={"save_default_payment_method": "on_subscription"},
        metadata={"user_id": str(user_id), "tier": tier},
        expand=["latest_invoice.payment_intent", "latest_invoice.confirmation_secret", "pending_setup_intent"],
    )

    latest_invoice = subscription.get("latest_invoice") or {}
    payment_intent = latest_invoice.get("payment_intent") or {}
    pending_setup_intent = subscription.get("pending_setup_intent") or {}
    confirmation_secret = latest_invoice.get("confirmation_secret") or {}

    client_secret = payment_intent.get("client_secret")
    intent_type = "payment"
    if not client_secret:
        client_secret = confirmation_secret.get("client_secret")
        intent_type = "payment"
    if not client_secret:
        client_secret = pending_setup_intent.get("client_secret")
        intent_type = "setup"
    if not client_secret and latest_invoice.get("id"):
        invoice = stripe.Invoice.retrieve(
            latest_invoice["id"],
            expand=["payment_intent", "confirmation_secret"],
        )
        invoice_payment_intent = invoice.get("payment_intent") or {}
        invoice_confirmation_secret = invoice.get("confirmation_secret") or {}
        client_secret = invoice_payment_intent.get("client_secret") or invoice_confirmation_secret.get("client_secret")
        intent_type = "payment"
    if not client_secret:
        status = str(subscription.get("status") or "unknown")
        raise ValueError(
            f"Unable to create subscription intent (subscription status: {status}, invoice: {latest_invoice.get('id', 'none')})."
        )

    _set_user_stripe_fields(user_id, customer_id, subscription.get("id"))
    return {
        "client_secret": client_secret,
        "intent_type": intent_type,
        "tier": tier,
        "subscription_id": subscription.get("id", ""),
    }


def process_stripe_webhook(payload: bytes, signature: str | None) -> dict[str, Any]:
    _require_stripe_config()
    if not STRIPE_WEBHOOK_SECRET:
        raise ValueError("Stripe webhook is not configured (missing STRIPE_WEBHOOK_SECRET).")
    if not signature:
        raise ValueError("Missing Stripe signature header.")

    event = stripe.Webhook.construct_event(payload=payload, sig_header=signature, secret=STRIPE_WEBHOOK_SECRET)
    event_type = event.get("type", "")
    data_object = (event.get("data") or {}).get("object") or {}

    if event_type == "checkout.session.completed":
        user_id_raw = (data_object.get("metadata") or {}).get("user_id")
        tier = (data_object.get("metadata") or {}).get("tier")
        customer_id = data_object.get("customer")
        subscription_id = data_object.get("subscription")
        if user_id_raw and tier in {"pro", "desk"}:
            user_id = int(user_id_raw)
            update_user_tier(user_id, tier, allow_upgrade=True)
            mark_tier_selection_complete(user_id)
            _set_user_stripe_fields(user_id, customer_id, subscription_id)
        return {"status": "processed", "event_type": event_type}

    if event_type in {"customer.subscription.updated", "customer.subscription.created"}:
        status = str(data_object.get("status") or "").lower()
        customer_id = data_object.get("customer")
        subscription_id = data_object.get("id")
        user_id_raw = (data_object.get("metadata") or {}).get("user_id")
        user_id = int(user_id_raw) if user_id_raw and str(user_id_raw).isdigit() else _resolve_user_id_for_customer(customer_id)
        if user_id:
            if status in {"active", "trialing", "past_due"}:
                tier = _extract_subscription_tier(data_object) or "pro"
                update_user_tier(user_id, tier, allow_upgrade=True)
                mark_tier_selection_complete(user_id)
            else:
                update_user_tier(user_id, "free", allow_upgrade=True)
            _set_user_stripe_fields(user_id, customer_id, subscription_id)
        return {"status": "processed", "event_type": event_type}

    if event_type in {"customer.subscription.deleted"}:
        customer_id = data_object.get("customer")
        user_id_raw = (data_object.get("metadata") or {}).get("user_id")
        user_id = int(user_id_raw) if user_id_raw and str(user_id_raw).isdigit() else _resolve_user_id_for_customer(customer_id)
        if user_id:
            update_user_tier(user_id, "free", allow_upgrade=True)
            _set_user_stripe_fields(user_id, customer_id, None)
        return {"status": "processed", "event_type": event_type}

    return {"status": "ignored", "event_type": event_type}

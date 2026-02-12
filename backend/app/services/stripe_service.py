"""Stripe payment service for subscription management."""

import logging

import stripe

from app.config import settings
from app.exceptions import PaymentError

logger = logging.getLogger("bookswipe")

stripe.api_key = settings.stripe_secret_key


def create_customer(email: str) -> str:
    """Create a Stripe customer and return the customer ID."""
    try:
        customer = stripe.Customer.create(email=email)
        return customer.id
    except stripe.StripeError as e:
        logger.error("Stripe create_customer failed: %s", str(e))
        raise PaymentError("Failed to create payment profile")


def create_checkout_session(customer_id: str, price_id: str) -> str:
    """Create a Stripe checkout session and return the URL."""
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=settings.stripe_success_url,
            cancel_url=settings.stripe_cancel_url,
        )
        return session.url
    except stripe.StripeError as e:
        logger.error("Stripe create_checkout_session failed: %s", str(e))
        raise PaymentError("Failed to create checkout session")


def create_billing_portal_session(customer_id: str) -> str:
    """Create a Stripe billing portal session and return the URL."""
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=settings.stripe_success_url,
        )
        return session.url
    except stripe.StripeError as e:
        logger.error("Stripe create_billing_portal_session failed: %s", str(e))
        raise PaymentError("Failed to create billing portal session")


def cancel_subscription(subscription_id: str) -> None:
    """Cancel a Stripe subscription at period end."""
    try:
        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )
    except stripe.StripeError as e:
        logger.error("Stripe cancel_subscription failed: %s", str(e))
        raise PaymentError("Failed to cancel subscription")


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify and construct a Stripe webhook event."""
    try:
        return stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.SignatureVerificationError:
        raise PaymentError("Invalid webhook signature")
    except ValueError:
        raise PaymentError("Invalid webhook payload")


from typing import Optional

import stripe

from app.src.stripe_services.stripe_client import stripe_client


class PaymentIntentService:

    def __init__(self, client: Optional[stripe.StripeClient] = None):
        self.client = client if client is not None else stripe_client

    # CREATE PAYMENT INTENT
    def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        capture_method: str = "automatic",
        metadata: Optional[dict] = None,
        idempotency_key: Optional[str] = None
    ):

        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("Amount must be a positive integer")

        if not isinstance(currency, str) or len(currency.strip()) != 3:
            raise ValueError("Currency must be a three-letter code")

        if capture_method not in ("automatic", "manual"):
            raise ValueError("Capture method must be automatic or manual")

        if customer_id is not None:
            if not isinstance(customer_id, str) or not customer_id.strip():
                raise ValueError("Customer ID cannot be empty")

        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")

        if idempotency_key is not None:
            if not isinstance(idempotency_key, str) or not idempotency_key.strip():
                raise ValueError("Idempotency key cannot be empty")

        params = {
            "amount": amount,
            "currency": currency.strip().lower(),
            "capture_method": capture_method,
            "automatic_payment_methods": {
                "enabled": True,
                "allow_redirects": "never"
            }
        }

        if customer_id is not None:
            params["customer"] = customer_id

        if metadata is not None:
            params["metadata"] = metadata

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key

        return self.client.v1.payment_intents.create(
            params=params,
            options=options
        )

    # RETRIEVE PAYMENT INTENT
    def retrieve_payment_intent(self, payment_intent_id: str):

        if not isinstance(payment_intent_id, str) or not payment_intent_id.strip():
            raise ValueError("Payment Intent ID cannot be empty")

        return self.client.v1.payment_intents.retrieve(payment_intent_id)

    # UPDATE PAYMENT INTENT
    def update_payment_intent(
        self,
        payment_intent_id: str,
        amount: Optional[int] = None,
        metadata: Optional[dict] = None,
        idempotency_key: Optional[str] = None
    ):

        if not isinstance(payment_intent_id, str) or not payment_intent_id.strip():
            raise ValueError("Payment Intent ID cannot be empty")

        params = {}

        if amount is not None:
            if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
                raise ValueError("Amount must be a positive integer")
            params["amount"] = amount

        if metadata is not None:
            if not isinstance(metadata, dict):
                raise ValueError("Metadata must be a dictionary")
            params["metadata"] = metadata

        if not params:
            raise ValueError("Provide an amount or metadata to update")

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key

        return self.client.v1.payment_intents.update(
            payment_intent_id,
            params=params,
            options=options
        )

    # CONFIRM PAYMENT INTENT
    def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ):

        if not isinstance(payment_intent_id, str) or not payment_intent_id.strip():
            raise ValueError("Payment Intent ID cannot be empty")

        params = {}

        if payment_method:
            params["payment_method"] = payment_method

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key

        return self.client.v1.payment_intents.confirm(
            payment_intent_id,
            params=params,
            options=options
        )

    # CAPTURE PAYMENT INTENT
    def capture_payment_intent(
        self,
        payment_intent_id: str,
        amount_to_capture: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ):

        if not isinstance(payment_intent_id, str) or not payment_intent_id.strip():
            raise ValueError("Payment Intent ID cannot be empty")

        params = {}

        if amount_to_capture is not None:
            if (
                not isinstance(amount_to_capture, int)
                or isinstance(amount_to_capture, bool)
                or amount_to_capture <= 0
            ):
                raise ValueError("Capture amount must be a positive integer")

            params["amount_to_capture"] = amount_to_capture

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key

        return self.client.v1.payment_intents.capture(
            payment_intent_id,
            params=params,
            options=options
        )

    # CANCEL PAYMENT INTENT
    def cancel_payment_intent(
        self,
        payment_intent_id: str,
        cancellation_reason: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ):

        if not isinstance(payment_intent_id, str) or not payment_intent_id.strip():
            raise ValueError("Payment Intent ID cannot be empty")

        params = {}

        if cancellation_reason:
            allowed_reasons = (
                "duplicate",
                "fraudulent",
                "requested_by_customer",
                "abandoned"
            )

            if cancellation_reason not in allowed_reasons:
                raise ValueError("Invalid cancellation reason")

            params["cancellation_reason"] = cancellation_reason

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key

        return self.client.v1.payment_intents.cancel(
            payment_intent_id,
            params=params,
            options=options
        )

    # LIST PAYMENT INTENTS
    def list_payment_intents(
        self,
        limit: int = 10,
        starting_after: Optional[str] = None,
        customer_id: Optional[str] = None
    ):

        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or not 1 <= limit <= 100
        ):
            raise ValueError("Limit must be between 1 and 100")

        params = {
            "limit": limit
        }

        if starting_after:
            params["starting_after"] = starting_after

        if customer_id:
            params["customer"] = customer_id

        return self.client.v1.payment_intents.list(params=params)


from typing import Optional

import stripe

from app.src.stripe_services.stripe_client import stripe_client


class SubscriptionService:

    def __init__(self, client: Optional[stripe.StripeClient] = None):
        # Use shared Stripe client; allow injection for unit tests.
        self.client = client if client is not None else stripe_client

    # CREATE SUBSCRIPTION
    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        quantity: int = 1,
        payment_behavior: str = "default_incomplete",
        metadata: Optional[dict] = None,
        idempotency_key: Optional[str] = None
    ):

        if not isinstance(customer_id, str) or not customer_id.strip():
            raise ValueError("Customer ID cannot be empty")

        if not isinstance(price_id, str) or not price_id.strip():
            raise ValueError("Price ID cannot be empty")

        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity <= 0
        ):
            raise ValueError("Quantity must be a positive integer")

        allowed_payment_behaviors = (
            "allow_incomplete",
            "default_incomplete",
            "error_if_incomplete"
        )

        if payment_behavior not in allowed_payment_behaviors:
            raise ValueError("Invalid payment behavior")

        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")

        if idempotency_key is not None:
            if not isinstance(idempotency_key, str) or not idempotency_key.strip():
                raise ValueError("Idempotency key cannot be empty")

        params = {
            "customer": customer_id.strip(),
            "items": [
                {
                    "price": price_id.strip(),
                    "quantity": quantity
                }
            ],
            "payment_behavior": payment_behavior
        }

        if metadata is not None:
            params["metadata"] = metadata

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key

        return self.client.v1.subscriptions.create(
            params=params,
            options=options
        )

    # RETRIEVE SUBSCRIPTION
    def retrieve_subscription(self, subscription_id: str):

        if (
            not isinstance(subscription_id, str)
            or not subscription_id.strip()
        ):
            raise ValueError("Subscription ID cannot be empty")

        return self.client.v1.subscriptions.retrieve(
            subscription_id.strip()
        )


    # UPDATE SUBSCRIPTION
    def update_subscription(
        self,
        subscription_id: str,
        metadata: Optional[dict] = None,
        price_id: Optional[str] = None,
        subscription_item_id: Optional[str] = None,
        quantity: Optional[int] = None,
        proration_behavior: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ):

        if (
            not isinstance(subscription_id, str)
            or not subscription_id.strip()
        ):
            raise ValueError("Subscription ID cannot be empty")

        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")

        if price_id is not None:
            if not isinstance(price_id, str) or not price_id.strip():
                raise ValueError("Price ID cannot be empty")

        if subscription_item_id is not None:
            if (
                not isinstance(subscription_item_id, str)
                or not subscription_item_id.strip()
            ):
                raise ValueError("Subscription item ID cannot be empty")

        if (
            (price_id is not None or quantity is not None)
            and subscription_item_id is None
        ):
            raise ValueError(
                "Subscription item ID is required when changing price or quantity"
            )

        if quantity is not None:
            if (
                not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or quantity <= 0
            ):
                raise ValueError("Quantity must be a positive integer")

        allowed_proration_behaviors = (
            "create_prorations",
            "none",
            "always_invoice"
        )

        if (
            proration_behavior is not None
            and proration_behavior not in allowed_proration_behaviors
        ):
            raise ValueError("Invalid proration behavior")

        if idempotency_key is not None:
            if (
                not isinstance(idempotency_key, str)
                or not idempotency_key.strip()
            ):
                raise ValueError("Idempotency key cannot be empty")

        params = {}

        if metadata is not None:
            params["metadata"] = metadata

        if price_id is not None or quantity is not None:

            item_update = {
                "id": subscription_item_id.strip()
            }

            if price_id is not None:
                item_update["price"] = price_id.strip()

            if quantity is not None:
                item_update["quantity"] = quantity

            params["items"] = [item_update]

        if proration_behavior is not None:
            params["proration_behavior"] = proration_behavior

        if not params:
            raise ValueError(
                "Provide metadata, price ID, quantity, or proration behavior to update"
            )

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key.strip()

        return self.client.v1.subscriptions.update(
            subscription_id.strip(),
            params=params,
            options=options
        )

    # CANCEL SUBSCRIPTION
    def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = False,
        idempotency_key: Optional[str] = None
    ):

        if (
            not isinstance(subscription_id, str)
            or not subscription_id.strip()
        ):
            raise ValueError("Subscription ID cannot be empty")

        if not isinstance(cancel_at_period_end, bool):
            raise ValueError("Cancel at period end must be a boolean")

        if idempotency_key is not None:
            if (
                not isinstance(idempotency_key, str)
                or not idempotency_key.strip()
            ):
                raise ValueError("Idempotency key cannot be empty")

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key

        if cancel_at_period_end:
            return self.client.v1.subscriptions.update(
                subscription_id.strip(),
                params={"cancel_at_period_end": True},
                options=options
            )

        return self.client.v1.subscriptions.cancel(
            subscription_id.strip(),
            params={},
            options=options
        )

    # LIST SUBSCRIPTIONS
    def list_subscriptions(
        self,
        limit: int = 10,
        starting_after: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[str] = None
    ):

        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or not 1 <= limit <= 100
        ):
            raise ValueError("Limit must be between 1 and 100")

        if starting_after is not None:
            if not isinstance(starting_after, str) or not starting_after.strip():
                raise ValueError("Starting after cannot be empty")

        if customer_id is not None:
            if not isinstance(customer_id, str) or not customer_id.strip():
                raise ValueError("Customer ID cannot be empty")

        allowed_statuses = (
            "incomplete",
            "incomplete_expired",
            "trialing",
            "active",
            "past_due",
            "canceled",
            "unpaid",
            "paused",
            "all"
        )

        if status is not None and status not in allowed_statuses:
            raise ValueError("Invalid subscription status")

        params = {
            "limit": limit
        }

        if starting_after:
            params["starting_after"] = starting_after.strip()

        if customer_id:
            params["customer"] = customer_id.strip()

        if status:
            params["status"] = status

        return self.client.v1.subscriptions.list(params=params)

    # RESUME SUBSCRIPTION
    def resume_subscription(
        self,
        subscription_id: str,
        idempotency_key: Optional[str] = None
    ):

        if (
            not isinstance(subscription_id, str)
            or not subscription_id.strip()
        ):
            raise ValueError("Subscription ID cannot be empty")

        if idempotency_key is not None:
            if (
                not isinstance(idempotency_key, str)
                or not idempotency_key.strip()
            ):
                raise ValueError("Idempotency key cannot be empty")

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key.strip()

        return self.client.v1.subscriptions.resume(
            subscription_id.strip(),
            params={},
            options=options
        )


    # RESUME PAYMENT COLLECTION
    def resume_collection(
        self,
        subscription_id: str,
        idempotency_key: Optional[str] = None
    ):

        if (
            not isinstance(subscription_id, str)
            or not subscription_id.strip()
        ):
            raise ValueError("Subscription ID cannot be empty")

        if idempotency_key is not None:
            if (
                not isinstance(idempotency_key, str)
                or not idempotency_key.strip()
            ):
                raise ValueError("Idempotency key cannot be empty")

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key.strip()

        return self.client.v1.subscriptions.update(
            subscription_id.strip(),
            params={"pause_collection": None},
            options=options
        )


    # PAUSE PAYMENT COLLECTION
    def pause_collection(
        self,
        subscription_id: str,
        behavior: str = "keep_as_draft",
        idempotency_key: Optional[str] = None
    ):

        if (
            not isinstance(subscription_id, str)
            or not subscription_id.strip()
        ):
            raise ValueError("Subscription ID cannot be empty")

        allowed_behaviors = (
            "keep_as_draft",
            "mark_uncollectible",
            "void"
        )

        if behavior not in allowed_behaviors:
            raise ValueError("Invalid pause collection behavior")

        if idempotency_key is not None:
            if (
                not isinstance(idempotency_key, str)
                or not idempotency_key.strip()
            ):
                raise ValueError("Idempotency key cannot be empty")

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key.strip()

        params = {
            "pause_collection": {
                "behavior": behavior
            }
        }

        return self.client.v1.subscriptions.update(
            subscription_id.strip(),
            params=params,
            options=options
        )

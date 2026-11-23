
from typing import Optional

import stripe

from app.src.stripe_services.stripe_client import stripe_client


class PriceService:

    def __init__(self, client: Optional[stripe.StripeClient] = None):
        # Use shared Stripe client; allow injection for unit tests.
        self.client = client if client is not None else stripe_client

    # CREATE PRICE
    def create_price(
        self,
        product_id: str,
        unit_amount: int,
        currency: str = "usd",
        recurring_interval: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ):

        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError("Product ID cannot be empty")

        if (
            not isinstance(unit_amount, int)
            or isinstance(unit_amount, bool)
            or unit_amount <= 0
        ):
            raise ValueError(
                "Unit amount must be a positive integer in the smallest currency unit"
            )

        if not isinstance(currency, str) or len(currency.strip()) != 3:
            raise ValueError("Currency must be a three-letter code")

        if recurring_interval is not None and recurring_interval not in (
            "day", "week", "month", "year"
        ):
            raise ValueError("Invalid recurring interval")

        params = {
            "product": product_id,
            "unit_amount": unit_amount,
            "currency": currency.lower()
        }

        if recurring_interval:
            params["recurring"] = {
                "interval": recurring_interval
            }

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key

        return self.client.v1.prices.create(
            params=params,
            options=options
        )

    # RETRIEVE PRICE
    def retrieve_price(self, price_id: str):

        if not isinstance(price_id, str) or not price_id.strip():
            raise ValueError("Price ID cannot be empty")

        return self.client.v1.prices.retrieve(price_id)

    # UPDATE PRICE METADATA
    def update_price(
        self,
        price_id: str,
        metadata: dict
    ):

        if not isinstance(price_id, str) or not price_id.strip():
            raise ValueError("Price ID cannot be empty")

        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")

        return self.client.v1.prices.update(
            price_id,
            params={
                "metadata": metadata
            }
        )

    # LIST PRICES
    def list_prices(
        self,
        limit: int = 10,
        starting_after: Optional[str] = None,
        product_id: Optional[str] = None,
        active: Optional[bool] = None
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

        if product_id:
            params["product"] = product_id

        if active is not None:
            params["active"] = active

        return self.client.v1.prices.list(params=params)

    # ARCHIVE PRICE
    def archive_price(self, price_id: str):

        if not isinstance(price_id, str) or not price_id.strip():
            raise ValueError("Price ID cannot be empty")

        return self.client.v1.prices.update(
            price_id,
            params={
                "active": False
            }
        )

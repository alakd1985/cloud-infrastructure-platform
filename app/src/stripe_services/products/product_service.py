
import stripe
from typing import Optional

from app.src.stripe_services.stripe_client import stripe_client


class ProductService:

    def __init__(self, client: Optional[stripe.StripeClient] = None):
        # Use shared Stripe client; allow injection for unit tests.
        self.client = client if client is not None else stripe_client

    # CREATE PRODUCT
    def create_product(
        self,
        name: str,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ):

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Product name cannot be empty")

        if description is not None and not isinstance(description, str):
            raise ValueError("Product description must be a string")

        params = {
            "name": name.strip()
        }

        if description is not None:
            params["description"] = description.strip()

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key

        return self.client.v1.products.create(
            params=params,
            options=options
        )

    # RETRIEVE PRODUCT
    def retrieve_product(self, product_id: str):

        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError("Product ID cannot be empty")

        return self.client.v1.products.retrieve(product_id)

    # UPDATE PRODUCT
    def update_product(
        self,
        product_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        active: Optional[bool] = None,
        idempotency_key: Optional[str] = None
    ):

        if not isinstance(product_id, str) or not product_id.strip():
            raise ValueError("Product ID cannot be empty")

        params = {}

        if name is not None:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Product name cannot be empty")

            params["name"] = name.strip()

        if description is not None:
            if not isinstance(description, str):
                raise ValueError("Product description must be a string")

            params["description"] = description.strip()

        if active is not None:
            if not isinstance(active, bool):
                raise ValueError("Active must be True or False")

            params["active"] = active

        if not params:
            raise ValueError("At least one product field must be updated")

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key

        return self.client.v1.products.update(
            product_id,
            params=params,
            options=options
        )

    # LIST PRODUCTS
    def list_products(
        self,
        limit: int = 10,
        starting_after: Optional[str] = None,
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

        if active is not None:
            params["active"] = active

        return self.client.v1.products.list(params=params)

    # ARCHIVE PRODUCT
    def archive_product(
        self,
        product_id: str,
        idempotency_key: Optional[str] = None
    ):

        return self.update_product(
            product_id=product_id,
            active=False,
            idempotency_key=idempotency_key
        )

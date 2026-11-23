
import stripe

from app.src.stripe_services.stripe_client import stripe_client


class CustomerService:

    def __init__(self, client: stripe.StripeClient | None = None):
        # Allow client injection for unit testing.
        self.client = client if client is not None else stripe_client

    def create_customer(
        self,
        name: str,
        email: str,
        idempotency_key: str | None = None,
    ):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Customer name cannot be empty")

        if not isinstance(email, str) or "@" not in email:
            raise ValueError("A valid email address is required")

        options = {}

        if idempotency_key:
            options["idempotency_key"] = idempotency_key

        return self.client.v1.customers.create(
            params={
                "name": name.strip(),
                "email": email.strip(),
            },
            options=options,
        )

    def retrieve_customer(self, customer_id: str):
        return self.client.v1.customers.retrieve(customer_id)

    def update_customer(self, customer_id: str, name: str, email: str):
        return self.client.v1.customers.update(
            customer_id,
            params={
                "name": name,
                "email": email,
            },
        )

    def list_customers(self, limit: int = 10, starting_after: str | None = None):
        params = {"limit": limit}

        if starting_after:
            params["starting_after"] = starting_after

        return self.client.v1.customers.list(params=params)

    def delete_customer(self, customer_id: str):
        return self.client.v1.customers.delete(customer_id)

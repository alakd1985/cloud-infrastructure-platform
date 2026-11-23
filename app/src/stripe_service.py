
import stripe
import uuid
from app.src.config import STRIPE_SECRET_KEY


def get_stripe_balance():
    client = stripe.StripeClient(STRIPE_SECRET_KEY)

    return client.v1.balance.retrieve()


def create_customer(name: str, email: str):
    client = stripe.StripeClient(STRIPE_SECRET_KEY)
    customer = client.v1.customers.create(
        params={
            "name": name,
            "email": email,
        }
    )

    return customer
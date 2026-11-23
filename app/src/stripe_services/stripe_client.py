
import stripe

from app.src.config import STRIPE_SECRET_KEY


def create_stripe_client() -> stripe.StripeClient:
    """
    Create a configured Stripe client.

    Uses Stripe SDK automatic retries for transient failures.
    """
    return stripe.StripeClient(
        STRIPE_SECRET_KEY,
        max_network_retries=2,
    )


stripe_client = create_stripe_client()

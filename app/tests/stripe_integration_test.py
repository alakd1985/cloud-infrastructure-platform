from app.src.stripe_service import get_stripe_balance, create_customer
import uuid
from app.src.stripe_services.customers.customer_service import CustomerService

def test_stripe_connection():
    balance = get_stripe_balance()

    assert balance.object == "balance"
    assert balance.available is not None
    assert balance.pending is not None

    print("\nSuccessfully connected to Stripe!")
    print(f"Available balance entries: {len(balance.available)}")
    print(f"Pending balance entries: {len(balance.pending)}")


def test_create_customer():
    service = CustomerService()

    unique_id = uuid.uuid4().hex[:8]
    email = f"test.customer.{unique_id}@example.com"

    customer = service.create_customer(
        name="Test Customer",
        email=email
    )

    assert customer.id.startswith("cus_")
    assert customer.name == "Test Customer"
    assert customer.email == email

    print(f"\nCustomer created: {customer.id}")
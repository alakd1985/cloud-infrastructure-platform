
import uuid

import pytest
import stripe

from app.src.stripe_services.payment_intents.payment_intent_service import (
    PaymentIntentService,
)
from app.src.stripe_services.customers.customer_service import CustomerService


def create_test_customer():
    customer_service = CustomerService()

    return customer_service.create_customer(
        name=f"Payment Test {uuid.uuid4().hex[:8]}",
        email=f"payment-{uuid.uuid4().hex[:8]}@example.com"
    )


def create_test_payment_intent(
    service,
    amount=2000,
    capture_method="automatic"
):
    return service.create_payment_intent(
        amount=amount,
        capture_method=capture_method
    )


# CREATE PAYMENT INTENT
def test_create_payment_intent():
    service = PaymentIntentService()

    intent = service.create_payment_intent(
        amount=2000,
        currency="usd",
        metadata={"order_id": "ORDER-001"}
    )

    assert intent.id.startswith("pi_")
    assert intent.amount == 2000
    assert intent.currency == "usd"
    assert intent.status == "requires_payment_method"
    assert intent.metadata["order_id"] == "ORDER-001"

    print(f"\nCreated Payment Intent: {intent.id}")


# CREATE PAYMENT INTENT FOR A CUSTOMER
def test_create_payment_intent_for_customer():
    service = PaymentIntentService()
    customer = create_test_customer()

    intent = service.create_payment_intent(
        amount=3500,
        customer_id=customer.id
    )

    assert intent.customer == customer.id
    assert intent.amount == 3500

    print(f"\nCustomer Payment Intent: {intent.id}")


# RETRIEVE PAYMENT INTENT
def test_retrieve_payment_intent():
    service = PaymentIntentService()

    created = create_test_payment_intent(service)

    retrieved = service.retrieve_payment_intent(created.id)

    assert retrieved.id == created.id
    assert retrieved.amount == 2000

    print(f"\nRetrieved Payment Intent: {retrieved.id}")


# INVALID PAYMENT INTENT ID
def test_retrieve_invalid_payment_intent():
    service = PaymentIntentService()

    with pytest.raises(stripe.InvalidRequestError):
        service.retrieve_payment_intent("pi_invalid123")


# UPDATE AMOUNT
def test_update_payment_intent_amount():
    service = PaymentIntentService()

    intent = create_test_payment_intent(service)

    updated = service.update_payment_intent(
        payment_intent_id=intent.id,
        amount=4500
    )

    assert updated.amount == 4500

    print(f"\nUpdated amount: {updated.amount}")


# UPDATE METADATA
def test_update_payment_intent_metadata():
    service = PaymentIntentService()

    intent = create_test_payment_intent(service)

    updated = service.update_payment_intent(
        payment_intent_id=intent.id,
        metadata={
            "order_id": "ORDER-002",
            "environment": "test"
        }
    )

    assert updated.metadata["order_id"] == "ORDER-002"
    assert updated.metadata["environment"] == "test"


# CONFIRM PAYMENT SUCCESSFULLY
def test_confirm_payment_intent():
    service = PaymentIntentService()

    intent = create_test_payment_intent(service)

    confirmed = service.confirm_payment_intent(
        payment_intent_id=intent.id,
        payment_method="pm_card_visa"
    )

    assert confirmed.status == "succeeded"

    print(f"\nPayment succeeded: {confirmed.id}")


# MANUAL AUTHORIZATION AND CAPTURE
def test_capture_payment_intent():
    service = PaymentIntentService()

    intent = create_test_payment_intent(
        service,
        amount=5000,
        capture_method="manual"
    )

    authorized = service.confirm_payment_intent(
        payment_intent_id=intent.id,
        payment_method="pm_card_visa"
    )

    assert authorized.status == "requires_capture"

    captured = service.capture_payment_intent(
        payment_intent_id=intent.id
    )

    assert captured.status == "succeeded"

    print(f"\nCaptured payment: {captured.id}")


# CANCEL PAYMENT INTENT
def test_cancel_payment_intent():
    service = PaymentIntentService()

    intent = create_test_payment_intent(service)

    canceled = service.cancel_payment_intent(
        payment_intent_id=intent.id,
        cancellation_reason="abandoned"
    )

    assert canceled.id == intent.id
    assert canceled.status == "canceled"

    print(f"\nCanceled payment: {canceled.id}")


# LIST PAYMENT INTENTS
def test_list_payment_intents():
    service = PaymentIntentService()
    customer = create_test_customer()

    created = service.create_payment_intent(
        amount=2500,
        customer_id=customer.id
    )

    result = service.list_payment_intents(
        limit=10,
        customer_id=customer.id
    )

    assert result.object == "list"

    intent_ids = [item.id for item in result.data]

    assert created.id in intent_ids

    print(f"\nPayment Intents returned: {len(result.data)}")


# PAGINATION
def test_list_payment_intents_pagination():
    service = PaymentIntentService()
    customer = create_test_customer()

    for amount in (1000, 2000, 3000):
        service.create_payment_intent(
            amount=amount,
            customer_id=customer.id
        )

    first_page = service.list_payment_intents(
        limit=2,
        customer_id=customer.id
    )

    assert len(first_page.data) == 2
    assert first_page.has_more is True

    last_id = first_page.data[-1].id

    second_page = service.list_payment_intents(
        limit=2,
        starting_after=last_id,
        customer_id=customer.id
    )

    assert len(second_page.data) >= 1

    first_ids = [item.id for item in first_page.data]
    second_ids = [item.id for item in second_page.data]

    assert not set(first_ids).intersection(second_ids)


# INVALID AMOUNT
def test_create_payment_intent_invalid_amount():
    service = PaymentIntentService()

    with pytest.raises(ValueError, match="Amount must be a positive integer"):
        service.create_payment_intent(amount=-100)


# INVALID CAPTURE METHOD
def test_create_payment_intent_invalid_capture_method():
    service = PaymentIntentService()

    with pytest.raises(ValueError, match="Capture method must be automatic or manual"):
        service.create_payment_intent(
            amount=2000,
            capture_method="invalid"
        )


# INVALID LIST LIMIT
def test_list_payment_intents_invalid_limit():
    service = PaymentIntentService()

    with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
        service.list_payment_intents(limit=101)


# UPDATE WITHOUT FIELDS
def test_update_payment_intent_without_fields():
    service = PaymentIntentService()

    with pytest.raises(ValueError, match="Provide an amount or metadata to update"):
        service.update_payment_intent(
            payment_intent_id="pi_test123"
        )


# IDEMPOTENCY
def test_create_payment_intent_idempotency():
    service = PaymentIntentService()

    idempotency_key = f"payment-{uuid.uuid4().hex}"

    first = service.create_payment_intent(
        amount=2000,
        idempotency_key=idempotency_key
    )

    second = service.create_payment_intent(
        amount=2000,
        idempotency_key=idempotency_key
    )

    assert first.id == second.id


from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import stripe

from app.src.stripe_services.payment_intents.payment_intent_service import (
    PaymentIntentService,
)


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def service(mock_client):
    return PaymentIntentService(client=mock_client)


def make_payment_intent(
    intent_id="pi_test123",
    amount=2000,
    currency="usd",
    status="requires_payment_method",
    customer=None,
    capture_method="automatic",
    metadata=None,
):
    return SimpleNamespace(
        id=intent_id,
        amount=amount,
        currency=currency,
        status=status,
        customer=customer,
        capture_method=capture_method,
        metadata=metadata or {},
    )


def make_payment_intent_list(intents, has_more=False):
    return SimpleNamespace(
        object="list",
        data=intents,
        has_more=has_more,
    )


# CREATE PAYMENT INTENT
def test_create_payment_intent(service, mock_client):
    expected = make_payment_intent(
        metadata={"order_id": "ORDER-001"}
    )
    mock_client.v1.payment_intents.create.return_value = expected

    intent = service.create_payment_intent(
        amount=2000,
        currency="usd",
        metadata={"order_id": "ORDER-001"},
    )

    assert intent.id == "pi_test123"
    assert intent.amount == 2000
    assert intent.currency == "usd"
    assert intent.status == "requires_payment_method"
    assert intent.metadata["order_id"] == "ORDER-001"

    mock_client.v1.payment_intents.create.assert_called_once_with(
        params={
            "amount": 2000,
            "currency": "usd",
            "capture_method": "automatic",
            "automatic_payment_methods": {
                "enabled": True,
                "allow_redirects": "never",
            },
            "metadata": {"order_id": "ORDER-001"},
        },
        options={},
    )


# CREATE PAYMENT INTENT FOR A CUSTOMER
def test_create_payment_intent_for_customer(service, mock_client):
    expected = make_payment_intent(
        amount=3500,
        customer="cus_test123",
    )
    mock_client.v1.payment_intents.create.return_value = expected

    intent = service.create_payment_intent(
        amount=3500,
        customer_id="cus_test123",
    )

    assert intent.customer == "cus_test123"
    assert intent.amount == 3500

    mock_client.v1.payment_intents.create.assert_called_once_with(
        params={
            "amount": 3500,
            "currency": "usd",
            "capture_method": "automatic",
            "automatic_payment_methods": {
                "enabled": True,
                "allow_redirects": "never",
            },
            "customer": "cus_test123",
        },
        options={},
    )


# RETRIEVE PAYMENT INTENT
def test_retrieve_payment_intent(service, mock_client):
    expected = make_payment_intent()

    mock_client.v1.payment_intents.retrieve.return_value = expected

    intent = service.retrieve_payment_intent("pi_test123")

    assert intent.id == "pi_test123"
    assert intent.amount == 2000

    mock_client.v1.payment_intents.retrieve.assert_called_once_with(
        "pi_test123"
    )


# INVALID PAYMENT INTENT ID
def test_retrieve_invalid_payment_intent(service, mock_client):
    error = stripe.InvalidRequestError(
        "No such payment intent",
        param="id",
    )

    mock_client.v1.payment_intents.retrieve.side_effect = error

    with pytest.raises(stripe.InvalidRequestError):
        service.retrieve_payment_intent("pi_invalid123")


# UPDATE AMOUNT
def test_update_payment_intent_amount(service, mock_client):
    expected = make_payment_intent(amount=4500)

    mock_client.v1.payment_intents.update.return_value = expected

    intent = service.update_payment_intent(
        payment_intent_id="pi_test123",
        amount=4500,
    )

    assert intent.amount == 4500

    mock_client.v1.payment_intents.update.assert_called_once_with(
        "pi_test123",
        params={"amount": 4500},
        options={},
    )


# UPDATE METADATA
def test_update_payment_intent_metadata(service, mock_client):
    metadata = {
        "order_id": "ORDER-002",
        "environment": "test",
    }

    expected = make_payment_intent(metadata=metadata)

    mock_client.v1.payment_intents.update.return_value = expected

    intent = service.update_payment_intent(
        payment_intent_id="pi_test123",
        metadata=metadata,
    )

    assert intent.metadata["order_id"] == "ORDER-002"
    assert intent.metadata["environment"] == "test"

    mock_client.v1.payment_intents.update.assert_called_once_with(
        "pi_test123",
        params={"metadata": metadata},
        options={},
    )


# CONFIRM PAYMENT SUCCESSFULLY
def test_confirm_payment_intent(service, mock_client):
    expected = make_payment_intent(status="succeeded")

    mock_client.v1.payment_intents.confirm.return_value = expected

    intent = service.confirm_payment_intent(
        payment_intent_id="pi_test123",
        payment_method="pm_card_visa",
    )

    assert intent.status == "succeeded"

    mock_client.v1.payment_intents.confirm.assert_called_once_with(
        "pi_test123",
        params={"payment_method": "pm_card_visa"},
        options={},
    )


# MANUAL AUTHORIZATION AND CAPTURE

def test_capture_payment_intent(service, mock_client):
    created = make_payment_intent(
        amount=5000,
        status="requires_payment_method",
        capture_method="manual",
    )

    authorized = make_payment_intent(
        amount=5000,
        status="requires_capture",
        capture_method="manual",
    )

    captured = make_payment_intent(
        amount=5000,
        status="succeeded",
        capture_method="manual",
    )

    mock_client.v1.payment_intents.create.return_value = created
    mock_client.v1.payment_intents.confirm.return_value = authorized
    mock_client.v1.payment_intents.capture.return_value = captured

    intent = service.create_payment_intent(
        amount=5000,
        capture_method="manual",
    )

    assert intent.id == "pi_test123"

    confirmed = service.confirm_payment_intent(
        payment_intent_id=intent.id,
        payment_method="pm_card_visa",
    )

    assert confirmed.status == "requires_capture"

    result = service.capture_payment_intent(
        payment_intent_id=intent.id,
    )

    assert result.status == "succeeded"

    mock_client.v1.payment_intents.capture.assert_called_once_with(
        "pi_test123",
        params={},
        options={},
    )

    assert result.status == "succeeded"

    mock_client.v1.payment_intents.capture.assert_called_once_with(
        "pi_test123",
        params={},
        options={},
    )


# CANCEL PAYMENT INTENT
def test_cancel_payment_intent(service, mock_client):
    expected = make_payment_intent(status="canceled")

    mock_client.v1.payment_intents.cancel.return_value = expected

    intent = service.cancel_payment_intent(
        payment_intent_id="pi_test123",
        cancellation_reason="abandoned",
    )

    assert intent.id == "pi_test123"
    assert intent.status == "canceled"

    mock_client.v1.payment_intents.cancel.assert_called_once_with(
        "pi_test123",
        params={"cancellation_reason": "abandoned"},
        options={},
    )


# LIST PAYMENT INTENTS
def test_list_payment_intents(service, mock_client):
    intents = [
        make_payment_intent(customer="cus_test123"),
        make_payment_intent(
            intent_id="pi_test456",
            customer="cus_test123",
        ),
    ]

    expected = make_payment_intent_list(intents)

    mock_client.v1.payment_intents.list.return_value = expected

    result = service.list_payment_intents(
        limit=10,
        customer_id="cus_test123",
    )

    assert result.object == "list"
    assert len(result.data) == 2

    mock_client.v1.payment_intents.list.assert_called_once_with(
        params={
            "limit": 10,
            "customer": "cus_test123",
        }
    )


# PAGINATION
def test_list_payment_intents_pagination(service, mock_client):
    first_page = make_payment_intent_list(
        [
            make_payment_intent("pi_1"),
            make_payment_intent("pi_2"),
        ],
        has_more=True,
    )

    second_page = make_payment_intent_list(
        [make_payment_intent("pi_3")],
        has_more=False,
    )

    mock_client.v1.payment_intents.list.side_effect = [
        first_page,
        second_page,
    ]

    page_one = service.list_payment_intents(
        limit=2,
        customer_id="cus_test123",
    )

    assert len(page_one.data) == 2
    assert page_one.has_more is True

    last_id = page_one.data[-1].id

    page_two = service.list_payment_intents(
        limit=2,
        starting_after=last_id,
        customer_id="cus_test123",
    )

    assert len(page_two.data) == 1

    first_ids = [item.id for item in page_one.data]
    second_ids = [item.id for item in page_two.data]

    assert not set(first_ids).intersection(second_ids)

    mock_client.v1.payment_intents.list.assert_any_call(
        params={
            "limit": 2,
            "customer": "cus_test123",
        }
    )

    mock_client.v1.payment_intents.list.assert_any_call(
        params={
            "limit": 2,
            "starting_after": "pi_2",
            "customer": "cus_test123",
        }
    )


# INVALID AMOUNT
def test_create_payment_intent_invalid_amount(service):
    with pytest.raises(
        ValueError,
        match="Amount must be a positive integer",
    ):
        service.create_payment_intent(amount=-100)


# INVALID CAPTURE METHOD
def test_create_payment_intent_invalid_capture_method(service):
    with pytest.raises(
        ValueError,
        match="Capture method must be automatic or manual",
    ):
        service.create_payment_intent(
            amount=2000,
            capture_method="invalid",
        )


# INVALID LIST LIMIT
def test_list_payment_intents_invalid_limit(service):
    with pytest.raises(
        ValueError,
        match="Limit must be between 1 and 100",
    ):
        service.list_payment_intents(limit=101)


# UPDATE WITHOUT FIELDS
def test_update_payment_intent_without_fields(service):
    with pytest.raises(
        ValueError,
        match="Provide an amount or metadata to update",
    ):
        service.update_payment_intent(
            payment_intent_id="pi_test123",
        )


# IDEMPOTENCY
def test_create_payment_intent_idempotency(service, mock_client):
    expected = make_payment_intent()

    mock_client.v1.payment_intents.create.return_value = expected

    idempotency_key = "payment-test-idempotency-123"

    first = service.create_payment_intent(
        amount=2000,
        idempotency_key=idempotency_key,
    )

    second = service.create_payment_intent(
        amount=2000,
        idempotency_key=idempotency_key,
    )

    assert first.id == second.id

    assert mock_client.v1.payment_intents.create.call_count == 2

    mock_client.v1.payment_intents.create.assert_called_with(
        params={
            "amount": 2000,
            "currency": "usd",
            "capture_method": "automatic",
            "automatic_payment_methods": {
                "enabled": True,
                "allow_redirects": "never",
            },
        },
        options={
            "idempotency_key": idempotency_key,
        },
    )

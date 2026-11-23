
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import stripe

from app.src.stripe_services.customers.customer_service import CustomerService


@pytest.fixture
def mock_client():
    """Create a mock Stripe client without making network requests."""
    client = MagicMock()
    return client


@pytest.fixture
def service(mock_client):
    return CustomerService(client=mock_client)


def make_customer(
    customer_id="cus_test123",
    name="John Smith",
    email="john@example.com",
    deleted=False,
):
    return SimpleNamespace(
        id=customer_id,
        name=name,
        email=email,
        deleted=deleted,
    )


def make_customer_list(customers, has_more=False):
    return SimpleNamespace(
        object="list",
        data=customers,
        has_more=has_more,
    )


def test_retrieve_customer(service, mock_client):
    expected = make_customer()

    mock_client.v1.customers.retrieve.return_value = expected

    customer = service.retrieve_customer("cus_test123")

    assert customer.id == "cus_test123"
    assert customer.name == "John Smith"
    mock_client.v1.customers.retrieve.assert_called_once_with(
        "cus_test123"
    )


def test_retrieve_invalid_customer(service, mock_client):
    error = stripe.InvalidRequestError(
        "No such customer: cus_invalid123",
        param="id",
    )

    mock_client.v1.customers.retrieve.side_effect = error

    with pytest.raises(stripe.InvalidRequestError):
        service.retrieve_customer("cus_invalid123")


def test_update_customer(service, mock_client):
    expected = make_customer(
        name="John Smith Updated",
        email="updated@example.com",
    )

    mock_client.v1.customers.update.return_value = expected

    customer = service.update_customer(
        customer_id="cus_test123",
        name="John Smith Updated",
        email="updated@example.com",
    )

    assert customer.id == "cus_test123"
    assert customer.name == "John Smith Updated"
    assert customer.email == "updated@example.com"

    mock_client.v1.customers.update.assert_called_once_with(
        "cus_test123",
        params={
            "name": "John Smith Updated",
            "email": "updated@example.com",
        },
    )


def test_list_customers(service, mock_client):
    customers = [
        make_customer("cus_1"),
        make_customer("cus_2"),
    ]

    expected = make_customer_list(customers)

    mock_client.v1.customers.list.return_value = expected

    result = service.list_customers(limit=10)

    assert result.object == "list"
    assert len(result.data) == 2
    assert result.data[0].id == "cus_1"

    mock_client.v1.customers.list.assert_called_once_with(
        params={"limit": 10}
    )


def test_list_customers_pagination(service, mock_client):
    first_page = make_customer_list(
        [
            make_customer("cus_1"),
            make_customer("cus_2"),
        ],
        has_more=True,
    )

    second_page = make_customer_list(
        [make_customer("cus_3")],
        has_more=False,
    )

    mock_client.v1.customers.list.side_effect = [
        first_page,
        second_page,
    ]

    page_one = service.list_customers(limit=2)

    assert len(page_one.data) == 2
    assert page_one.has_more is True

    last_customer_id = page_one.data[-1].id

    page_two = service.list_customers(
        limit=2,
        starting_after=last_customer_id,
    )

    assert len(page_two.data) == 1
    assert page_two.data[0].id == "cus_3"

    assert mock_client.v1.customers.list.call_count == 2

    mock_client.v1.customers.list.assert_any_call(
        params={"limit": 2}
    )

    mock_client.v1.customers.list.assert_any_call(
        params={
            "limit": 2,
            "starting_after": "cus_2",
        }
    )


def test_delete_customer(service, mock_client):
    expected = make_customer(deleted=True)

    mock_client.v1.customers.delete.return_value = expected

    customer = service.delete_customer("cus_test123")

    assert customer.id == "cus_test123"
    assert customer.deleted is True

    mock_client.v1.customers.delete.assert_called_once_with(
        "cus_test123"
    )


def test_create_customer_empty_name(service):
    with pytest.raises(
        ValueError,
        match="Customer name cannot be empty",
    ):
        service.create_customer(
            name="   ",
            email="test@example.com",
        )


def test_create_customer_invalid_email(service):
    with pytest.raises(
        ValueError,
        match="A valid email address is required",
    ):
        service.create_customer(
            name="John Smith",
            email="invalid-email",
        )


def test_create_customer_strips_whitespace(service, mock_client):
    expected = make_customer()

    mock_client.v1.customers.create.return_value = expected

    customer = service.create_customer(
        name="  John Smith  ",
        email="  john@example.com  ",
    )

    assert customer.name == "John Smith"
    assert customer.email == "john@example.com"

    mock_client.v1.customers.create.assert_called_once_with(
        params={
            "name": "John Smith",
            "email": "john@example.com",
        },
        options={},
    )


def test_create_customer_missing_name(service):
    with pytest.raises(
        ValueError,
        match="Customer name cannot be empty",
    ):
        service.create_customer(
            name=None,
            email="test@example.com",
        )


def test_create_customer_missing_email(service):
    with pytest.raises(
        ValueError,
        match="A valid email address is required",
    ):
        service.create_customer(
            name="John Smith",
            email=None,
        )


def test_stripe_authentication_error(service, mock_client):
    error = stripe.AuthenticationError(
        "Invalid API Key provided",
        http_status=401,
    )

    mock_client.v1.customers.list.side_effect = error

    with pytest.raises(stripe.AuthenticationError):
        service.list_customers(limit=1)


def test_create_customer_with_idempotency_key(service, mock_client):
    expected = make_customer()

    mock_client.v1.customers.create.return_value = expected

    idempotency_key = "customer-test-idempotency-123"

    first_customer = service.create_customer(
        name="Idempotency Test Customer",
        email="idempotency@example.com",
        idempotency_key=idempotency_key,
    )

    second_customer = service.create_customer(
        name="Idempotency Test Customer",
        email="idempotency@example.com",
        idempotency_key=idempotency_key,
    )

    assert first_customer.id == second_customer.id

    assert mock_client.v1.customers.create.call_count == 2

    mock_client.v1.customers.create.assert_called_with(
        params={
            "name": "Idempotency Test Customer",
            "email": "idempotency@example.com",
        },
        options={
            "idempotency_key": idempotency_key,
        },
    )

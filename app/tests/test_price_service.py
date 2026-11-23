
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import stripe

from app.src.stripe_services.prices.price_service import PriceService


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def service(mock_client):
    return PriceService(client=mock_client)


def make_price(
    price_id="price_test123",
    product="prod_test123",
    unit_amount=2000,
    currency="usd",
    interval=None,
    active=True,
    metadata=None,
):
    recurring = (
        SimpleNamespace(interval=interval)
        if interval is not None
        else None
    )

    return SimpleNamespace(
        id=price_id,
        product=product,
        unit_amount=unit_amount,
        currency=currency,
        type="recurring" if interval else "one_time",
        recurring=recurring,
        active=active,
        metadata=metadata or {},
    )


def make_price_list(prices, has_more=False):
    return SimpleNamespace(
        object="list",
        data=prices,
        has_more=has_more,
    )


# CREATE ONE-TIME PRICE
def test_create_one_time_price(service, mock_client):
    expected = make_price()
    mock_client.v1.prices.create.return_value = expected

    price = service.create_price(
        product_id="prod_test123",
        unit_amount=2000,
        currency="usd",
    )

    assert price.product == "prod_test123"
    assert price.unit_amount == 2000
    assert price.currency == "usd"
    assert price.type == "one_time"

    mock_client.v1.prices.create.assert_called_once_with(
        params={
            "product": "prod_test123",
            "unit_amount": 2000,
            "currency": "usd",
        },
        options={},
    )


# CREATE MONTHLY RECURRING PRICE
def test_create_monthly_price(service, mock_client):
    expected = make_price(interval="month")
    mock_client.v1.prices.create.return_value = expected

    price = service.create_price(
        product_id="prod_test123",
        unit_amount=2000,
        currency="usd",
        recurring_interval="month",
    )

    assert price.product == "prod_test123"
    assert price.unit_amount == 2000
    assert price.recurring.interval == "month"

    mock_client.v1.prices.create.assert_called_once_with(
        params={
            "product": "prod_test123",
            "unit_amount": 2000,
            "currency": "usd",
            "recurring": {"interval": "month"},
        },
        options={},
    )


# CREATE YEARLY RECURRING PRICE
def test_create_yearly_price(service, mock_client):
    expected = make_price(
        unit_amount=20000,
        interval="year",
    )
    mock_client.v1.prices.create.return_value = expected

    price = service.create_price(
        product_id="prod_test123",
        unit_amount=20000,
        currency="usd",
        recurring_interval="year",
    )

    assert price.recurring.interval == "year"
    assert price.unit_amount == 20000

    mock_client.v1.prices.create.assert_called_once_with(
        params={
            "product": "prod_test123",
            "unit_amount": 20000,
            "currency": "usd",
            "recurring": {"interval": "year"},
        },
        options={},
    )


# RETRIEVE PRICE
def test_retrieve_price(service, mock_client):
    expected = make_price(unit_amount=1500)
    mock_client.v1.prices.retrieve.return_value = expected

    price = service.retrieve_price("price_test123")

    assert price.id == "price_test123"
    assert price.unit_amount == 1500

    mock_client.v1.prices.retrieve.assert_called_once_with(
        "price_test123"
    )


# INVALID PRICE ID
def test_retrieve_invalid_price(service, mock_client):
    error = stripe.InvalidRequestError(
        "No such price",
        param="id",
    )
    mock_client.v1.prices.retrieve.side_effect = error

    with pytest.raises(stripe.InvalidRequestError):
        service.retrieve_price("price_invalid123")


# UPDATE PRICE METADATA
def test_update_price_metadata(service, mock_client):
    metadata = {
        "plan": "premium",
        "environment": "test",
    }

    expected = make_price(metadata=metadata)
    mock_client.v1.prices.update.return_value = expected

    price = service.update_price(
        price_id="price_test123",
        metadata=metadata,
    )

    assert price.metadata["plan"] == "premium"
    assert price.metadata["environment"] == "test"

    mock_client.v1.prices.update.assert_called_once_with(
        "price_test123",
        params={"metadata": metadata},
    )


# LIST PRICES
def test_list_prices(service, mock_client):
    prices = [
        make_price("price_1"),
        make_price("price_2"),
    ]

    expected = make_price_list(prices)
    mock_client.v1.prices.list.return_value = expected

    result = service.list_prices(
        limit=100,
        product_id="prod_test123",
    )

    assert result.object == "list"

    price_ids = [price.id for price in result.data]
    assert "price_1" in price_ids

    mock_client.v1.prices.list.assert_called_once_with(
        params={
            "limit": 100,
            "product": "prod_test123",
        }
    )


# PAGINATION
def test_list_prices_pagination(service, mock_client):
    first_page = make_price_list(
        [
            make_price("price_1"),
            make_price("price_2"),
        ],
        has_more=True,
    )

    second_page = make_price_list(
        [make_price("price_3")],
        has_more=False,
    )

    mock_client.v1.prices.list.side_effect = [
        first_page,
        second_page,
    ]

    page_one = service.list_prices(
        limit=2,
        product_id="prod_test123",
    )

    assert len(page_one.data) == 2
    assert page_one.has_more is True

    last_price_id = page_one.data[-1].id

    page_two = service.list_prices(
        limit=2,
        starting_after=last_price_id,
        product_id="prod_test123",
    )

    assert len(page_two.data) >= 1

    first_ids = [price.id for price in page_one.data]
    second_ids = [price.id for price in page_two.data]

    assert not set(first_ids).intersection(second_ids)

    mock_client.v1.prices.list.assert_any_call(
        params={
            "limit": 2,
            "product": "prod_test123",
        }
    )

    mock_client.v1.prices.list.assert_any_call(
        params={
            "limit": 2,
            "starting_after": "price_2",
            "product": "prod_test123",
        }
    )


# ARCHIVE PRICE
def test_archive_price(service, mock_client):
    expected = make_price(active=False)
    mock_client.v1.prices.update.return_value = expected

    price = service.archive_price("price_test123")

    assert price.id == "price_test123"
    assert price.active is False

    mock_client.v1.prices.update.assert_called_once_with(
        "price_test123",
        params={"active": False},
    )


# INPUT VALIDATION
def test_create_price_empty_product_id(service):
    with pytest.raises(
        ValueError,
        match="Product ID cannot be empty",
    ):
        service.create_price(
            product_id=" ",
            unit_amount=2000,
        )


def test_create_price_invalid_amount(service):
    with pytest.raises(
        ValueError,
        match="Unit amount must be a positive integer",
    ):
        service.create_price(
            product_id="prod_test123",
            unit_amount=-100,
        )


def test_create_price_invalid_interval(service):
    with pytest.raises(
        ValueError,
        match="Invalid recurring interval",
    ):
        service.create_price(
            product_id="prod_test123",
            unit_amount=2000,
            recurring_interval="hour",
        )


def test_list_prices_invalid_limit(service):
    with pytest.raises(
        ValueError,
        match="Limit must be between 1 and 100",
    ):
        service.list_prices(limit=101)


# IDEMPOTENCY
def test_create_price_idempotency(service, mock_client):
    expected = make_price()
    mock_client.v1.prices.create.return_value = expected

    idempotency_key = "price-test-idempotency-123"

    first = service.create_price(
        product_id="prod_test123",
        unit_amount=2000,
        idempotency_key=idempotency_key,
    )

    second = service.create_price(
        product_id="prod_test123",
        unit_amount=2000,
        idempotency_key=idempotency_key,
    )

    assert first.id == second.id
    assert mock_client.v1.prices.create.call_count == 2

    mock_client.v1.prices.create.assert_called_with(
        params={
            "product": "prod_test123",
            "unit_amount": 2000,
            "currency": "usd",
        },
        options={
            "idempotency_key": idempotency_key,
        },
    )


import uuid
import pytest
import stripe

from app.src.stripe_services.prices.price_service import PriceService
from app.src.stripe_services.products.product_service import ProductService


def create_test_product():
    product_service = ProductService()

    return product_service.create_product(
        name=f"Price Test Product {uuid.uuid4().hex[:8]}"
    )


# CREATE ONE-TIME PRICE
def test_create_one_time_price():
    service = PriceService()
    product = create_test_product()

    price = service.create_price(
        product_id=product.id,
        unit_amount=2000,
        currency="usd"
    )

    assert price.product == product.id
    assert price.unit_amount == 2000
    assert price.currency == "usd"
    assert price.type == "one_time"

    print(f"\nCreated one-time price: {price.id}")


# CREATE MONTHLY RECURRING PRICE
def test_create_monthly_price():
    service = PriceService()
    product = create_test_product()

    price = service.create_price(
        product_id=product.id,
        unit_amount=2000,
        currency="usd",
        recurring_interval="month"
    )

    assert price.product == product.id
    assert price.unit_amount == 2000
    assert price.recurring.interval == "month"

    print(f"\nCreated monthly price: {price.id}")


# CREATE YEARLY RECURRING PRICE
def test_create_yearly_price():
    service = PriceService()
    product = create_test_product()

    price = service.create_price(
        product_id=product.id,
        unit_amount=20000,
        currency="usd",
        recurring_interval="year"
    )

    assert price.recurring.interval == "year"
    assert price.unit_amount == 20000

    print(f"\nCreated yearly price: {price.id}")


# RETRIEVE PRICE
def test_retrieve_price():
    service = PriceService()
    product = create_test_product()

    created_price = service.create_price(
        product_id=product.id,
        unit_amount=1500
    )

    retrieved_price = service.retrieve_price(created_price.id)

    assert retrieved_price.id == created_price.id
    assert retrieved_price.unit_amount == 1500

    print(f"\nRetrieved price: {retrieved_price.id}")


# INVALID PRICE ID
def test_retrieve_invalid_price():
    service = PriceService()

    with pytest.raises(stripe.InvalidRequestError):
        service.retrieve_price("price_invalid123")


# UPDATE PRICE METADATA
def test_update_price_metadata():
    service = PriceService()
    product = create_test_product()

    price = service.create_price(
        product_id=product.id,
        unit_amount=3000
    )

    updated_price = service.update_price(
        price_id=price.id,
        metadata={
            "plan": "premium",
            "environment": "test"
        }
    )

    assert updated_price.metadata["plan"] == "premium"
    assert updated_price.metadata["environment"] == "test"

    print(f"\nUpdated price metadata: {updated_price.id}")


# LIST PRICES
def test_list_prices():
    service = PriceService()
    product = create_test_product()

    new_price = service.create_price(
        product_id=product.id,
        unit_amount=2500
    )

    price_list = service.list_prices(
        limit=100,
        product_id=product.id
    )

    assert price_list.object == "list"

    price_ids = [
        price.id for price in price_list.data
    ]

    assert new_price.id in price_ids

    print(f"\nPrices returned: {len(price_list.data)}")


# PAGINATION
def test_list_prices_pagination():
    service = PriceService()
    product = create_test_product()

    for amount in (1000, 2000, 3000):
        service.create_price(
            product_id=product.id,
            unit_amount=amount
        )

    first_page = service.list_prices(
        limit=2,
        product_id=product.id
    )

    assert len(first_page.data) == 2
    assert first_page.has_more is True

    last_price_id = first_page.data[-1].id

    second_page = service.list_prices(
        limit=2,
        starting_after=last_price_id,
        product_id=product.id
    )

    assert len(second_page.data) >= 1

    first_ids = [price.id for price in first_page.data]
    second_ids = [price.id for price in second_page.data]

    assert not set(first_ids).intersection(second_ids)


# ARCHIVE PRICE
def test_archive_price():
    service = PriceService()
    product = create_test_product()

    price = service.create_price(
        product_id=product.id,
        unit_amount=4000
    )

    archived_price = service.archive_price(price.id)

    assert archived_price.id == price.id
    assert archived_price.active is False

    print(f"\nArchived price: {archived_price.id}")


# INPUT VALIDATION
def test_create_price_empty_product_id():
    service = PriceService()

    with pytest.raises(ValueError, match="Product ID cannot be empty"):
        service.create_price(
            product_id=" ",
            unit_amount=2000
        )


def test_create_price_invalid_amount():
    service = PriceService()

    with pytest.raises(ValueError, match="Unit amount must be a positive integer"):
        service.create_price(
            product_id="prod_test",
            unit_amount=-100
        )


def test_create_price_invalid_interval():
    service = PriceService()

    with pytest.raises(ValueError, match="Invalid recurring interval"):
        service.create_price(
            product_id="prod_test",
            unit_amount=2000,
            recurring_interval="hour"
        )


def test_list_prices_invalid_limit():
    service = PriceService()

    with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
        service.list_prices(limit=101)


# IDEMPOTENCY
def test_create_price_idempotency():
    service = PriceService()
    product = create_test_product()

    idempotency_key = f"price-{uuid.uuid4().hex}"

    first_price = service.create_price(
        product_id=product.id,
        unit_amount=2000,
        idempotency_key=idempotency_key
    )

    second_price = service.create_price(
        product_id=product.id,
        unit_amount=2000,
        idempotency_key=idempotency_key
    )

    assert first_price.id == second_price.id

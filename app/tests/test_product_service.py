
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import stripe

from app.src.stripe_services.products.product_service import ProductService


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def service(mock_client):
    return ProductService(client=mock_client)


def make_product(
    product_id="prod_test123",
    name="Premium Membership",
    description="Premium monthly membership",
    active=True,
):
    return SimpleNamespace(
        id=product_id,
        name=name,
        description=description,
        active=active,
    )


def make_product_list(products, has_more=False):
    return SimpleNamespace(
        object="list",
        data=products,
        has_more=has_more,
    )


# CREATE PRODUCT
def test_create_product(service, mock_client):
    expected = make_product()
    mock_client.v1.products.create.return_value = expected

    product = service.create_product(
        name="Premium Membership",
        description="Premium monthly membership",
    )

    assert product.name == "Premium Membership"
    assert product.description == "Premium monthly membership"
    assert product.active is True

    mock_client.v1.products.create.assert_called_once_with(
        params={
            "name": "Premium Membership",
            "description": "Premium monthly membership",
        },
        options={},
    )


# RETRIEVE PRODUCT
def test_retrieve_product(service, mock_client):
    expected = make_product(
        name="Retrieve Test Product",
        description=None,
    )
    mock_client.v1.products.retrieve.return_value = expected

    product = service.retrieve_product("prod_test123")

    assert product.id == "prod_test123"
    assert product.name == "Retrieve Test Product"

    mock_client.v1.products.retrieve.assert_called_once_with(
        "prod_test123"
    )


# RETRIEVE INVALID PRODUCT
def test_retrieve_invalid_product(service, mock_client):
    error = stripe.InvalidRequestError(
        "No such product",
        param="id",
    )
    mock_client.v1.products.retrieve.side_effect = error

    with pytest.raises(stripe.InvalidRequestError):
        service.retrieve_product("prod_invalid123")


# UPDATE PRODUCT
def test_update_product(service, mock_client):
    expected = make_product(
        name="Updated Product",
        description="Updated product description",
    )
    mock_client.v1.products.update.return_value = expected

    product = service.update_product(
        product_id="prod_test123",
        name="Updated Product",
        description="Updated product description",
    )

    assert product.id == "prod_test123"
    assert product.name == "Updated Product"
    assert product.description == "Updated product description"

    mock_client.v1.products.update.assert_called_once_with(
        "prod_test123",
        params={
            "name": "Updated Product",
            "description": "Updated product description",
        },
        options={},
    )


# LIST PRODUCTS
def test_list_products(service, mock_client):
    products = [
        make_product("prod_1"),
        make_product("prod_2"),
    ]
    expected = make_product_list(products)

    mock_client.v1.products.list.return_value = expected

    result = service.list_products(limit=100)

    assert result.object == "list"
    assert len(result.data) <= 100

    product_ids = [product.id for product in result.data]
    assert "prod_1" in product_ids

    mock_client.v1.products.list.assert_called_once_with(
        params={"limit": 100}
    )


# PAGINATION
def test_list_products_pagination(service, mock_client):
    first_page = make_product_list(
        [
            make_product("prod_1"),
            make_product("prod_2"),
        ],
        has_more=True,
    )

    second_page = make_product_list(
        [make_product("prod_3")],
        has_more=False,
    )

    mock_client.v1.products.list.side_effect = [
        first_page,
        second_page,
    ]

    page_one = service.list_products(limit=2)

    assert len(page_one.data) == 2
    assert page_one.has_more is True

    last_product_id = page_one.data[-1].id

    page_two = service.list_products(
        limit=2,
        starting_after=last_product_id,
    )

    assert len(page_two.data) >= 1

    first_ids = [product.id for product in page_one.data]
    second_ids = [product.id for product in page_two.data]

    assert not set(first_ids).intersection(second_ids)

    mock_client.v1.products.list.assert_any_call(
        params={"limit": 2}
    )

    mock_client.v1.products.list.assert_any_call(
        params={
            "limit": 2,
            "starting_after": "prod_2",
        }
    )


# ARCHIVE PRODUCT
def test_archive_product(service, mock_client):
    expected = make_product(active=False)
    mock_client.v1.products.update.return_value = expected

    product = service.archive_product(
        product_id="prod_test123"
    )

    assert product.id == "prod_test123"
    assert product.active is False

    mock_client.v1.products.update.assert_called_once_with(
        "prod_test123",
        params={"active": False},
        options={},
    )


# INPUT VALIDATION: EMPTY NAME
def test_create_product_empty_name(service):
    with pytest.raises(
        ValueError,
        match="Product name cannot be empty",
    ):
        service.create_product(name=" ")


# INPUT VALIDATION: MISSING NAME
def test_create_product_missing_name(service):
    with pytest.raises(
        ValueError,
        match="Product name cannot be empty",
    ):
        service.create_product(name=None)


# INPUT VALIDATION: INVALID LIMIT
def test_list_products_invalid_limit(service):
    with pytest.raises(
        ValueError,
        match="Limit must be between 1 and 100",
    ):
        service.list_products(limit=101)


# IDEMPOTENCY
def test_create_product_idempotency(service, mock_client):
    expected = make_product(
        name="Idempotency Test Product",
        description="Testing product idempotency",
    )
    mock_client.v1.products.create.return_value = expected

    idempotency_key = "product-test-idempotency-123"

    first = service.create_product(
        name="Idempotency Test Product",
        description="Testing product idempotency",
        idempotency_key=idempotency_key,
    )

    second = service.create_product(
        name="Idempotency Test Product",
        description="Testing product idempotency",
        idempotency_key=idempotency_key,
    )

    assert first.id == second.id
    assert mock_client.v1.products.create.call_count == 2

    mock_client.v1.products.create.assert_called_with(
        params={
            "name": "Idempotency Test Product",
            "description": "Testing product idempotency",
        },
        options={
            "idempotency_key": idempotency_key,
        },
    )

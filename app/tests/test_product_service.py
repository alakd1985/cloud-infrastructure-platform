
import uuid
import pytest
import stripe

from app.src.stripe_services.products.product_service import ProductService


# CREATE PRODUCT
def test_create_product():
    service = ProductService()

    product = service.create_product(
        name="Premium Membership",
        description="Premium monthly membership"
    )

    assert product.name == "Premium Membership"
    assert product.description == "Premium monthly membership"
    assert product.active is True

    print(f"\nCreated product: {product.id}")


# RETRIEVE PRODUCT
def test_retrieve_product():
    service = ProductService()

    created_product = service.create_product(
        name="Retrieve Test Product"
    )

    retrieved_product = service.retrieve_product(
        created_product.id
    )

    assert retrieved_product.id == created_product.id
    assert retrieved_product.name == "Retrieve Test Product"

    print(f"\nRetrieved product: {retrieved_product.id}")


# RETRIEVE INVALID PRODUCT
def test_retrieve_invalid_product():
    service = ProductService()

    with pytest.raises(stripe.InvalidRequestError):
        service.retrieve_product("prod_invalid123")


# UPDATE PRODUCT
def test_update_product():
    service = ProductService()

    product = service.create_product(
        name="Original Product"
    )

    updated_product = service.update_product(
        product_id=product.id,
        name="Updated Product",
        description="Updated product description"
    )

    assert updated_product.id == product.id
    assert updated_product.name == "Updated Product"
    assert updated_product.description == "Updated product description"

    print(f"\nUpdated product: {updated_product.id}")


# LIST PRODUCTS
def test_list_products():
    service = ProductService()

    new_product = service.create_product(
        name="List Test Product"
    )

    product_list = service.list_products(limit=100)

    assert product_list.object == "list"
    assert len(product_list.data) <= 100

    product_ids = [
        product.id for product in product_list.data
    ]

    assert new_product.id in product_ids

    print(f"\nProducts returned: {len(product_list.data)}")


# PAGINATION
def test_list_products_pagination():
    service = ProductService()

    created_products = []

    for number in range(3):
        product = service.create_product(
            name=f"Pagination Product {number}"
        )

        created_products.append(product)

    first_page = service.list_products(limit=2)

    assert len(first_page.data) == 2
    assert first_page.has_more is True

    last_product_id = first_page.data[-1].id

    second_page = service.list_products(
        limit=2,
        starting_after=last_product_id
    )

    assert len(second_page.data) >= 1

    first_page_ids = [
        product.id for product in first_page.data
    ]

    second_page_ids = [
        product.id for product in second_page.data
    ]

    assert not set(first_page_ids).intersection(second_page_ids)

    print(f"\nFirst page: {first_page_ids}")
    print(f"Second page: {second_page_ids}")


# ARCHIVE PRODUCT
def test_archive_product():
    service = ProductService()

    product = service.create_product(
        name="Archive Test Product"
    )

    archived_product = service.archive_product(
        product_id=product.id
    )

    assert archived_product.id == product.id
    assert archived_product.active is False

    print(f"\nArchived product: {archived_product.id}")


# INPUT VALIDATION: EMPTY NAME
def test_create_product_empty_name():
    service = ProductService()

    with pytest.raises(
        ValueError,
        match="Product name cannot be empty"
    ):
        service.create_product(
            name=" "
        )


# INPUT VALIDATION: MISSING NAME
def test_create_product_missing_name():
    service = ProductService()

    with pytest.raises(
        ValueError,
        match="Product name cannot be empty"
    ):
        service.create_product(
            name=None
        )


# INPUT VALIDATION: INVALID LIMIT
def test_list_products_invalid_limit():
    service = ProductService()

    with pytest.raises(
        ValueError,
        match="Limit must be between 1 and 100"
    ):
        service.list_products(limit=101)


# IDEMPOTENCY
def test_create_product_idempotency():
    service = ProductService()

    idempotency_key = f"product-{uuid.uuid4().hex}"

    first_product = service.create_product(
        name="Idempotency Test Product",
        description="Testing product idempotency",
        idempotency_key=idempotency_key
    )

    second_product = service.create_product(
        name="Idempotency Test Product",
        description="Testing product idempotency",
        idempotency_key=idempotency_key
    )

    assert first_product.id == second_product.id

    print(f"\nProduct ID: {first_product.id}")
    print("Product idempotency verified")

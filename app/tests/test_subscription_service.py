from unittest.mock import MagicMock

import pytest

from app.src.stripe_services.subscriptions.subscription_service import (
    SubscriptionService,
)


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def subscription_service(mock_client):
    return SubscriptionService(client=mock_client)


# CREATE SUBSCRIPTION TESTS

def test_create_subscription_success(
        subscription_service,
        mock_client
):
    mock_response = MagicMock()
    mock_client.v1.subscriptions.create.return_value = mock_response

    result = subscription_service.create_subscription(
        customer_id="cus_12345",
        price_id="price_12345"
    )

    assert result == mock_response

    mock_client.v1.subscriptions.create.assert_called_once_with(
        params={
            "customer": "cus_12345",
            "items": [
                {
                    "price": "price_12345",
                    "quantity": 1
                }
            ],
            "payment_behavior": "default_incomplete"
        },
        options={}
    )


def test_create_subscription_with_custom_quantity(
        subscription_service,
        mock_client
):
    subscription_service.create_subscription(
        customer_id="cus_12345",
        price_id="price_12345",
        quantity=3
    )

    params = mock_client.v1.subscriptions.create.call_args.kwargs["params"]

    assert params["items"][0]["quantity"] == 3


def test_create_subscription_with_metadata(
        subscription_service,
        mock_client
):
    metadata = {"plan": "premium"}

    subscription_service.create_subscription(
        customer_id="cus_12345",
        price_id="price_12345",
        metadata=metadata
    )

    params = mock_client.v1.subscriptions.create.call_args.kwargs["params"]

    assert params["metadata"] == metadata


def test_create_subscription_with_idempotency_key(
        subscription_service,
        mock_client
):
    subscription_service.create_subscription(
        customer_id="cus_12345",
        price_id="price_12345",
        idempotency_key="subscription_order_123"
    )

    options = mock_client.v1.subscriptions.create.call_args.kwargs["options"]

    assert options["idempotency_key"] == "subscription_order_123"


def test_create_subscription_with_custom_payment_behavior(
        subscription_service,
        mock_client
):
    subscription_service.create_subscription(
        customer_id="cus_12345",
        price_id="price_12345",
        payment_behavior="allow_incomplete"
    )

    params = mock_client.v1.subscriptions.create.call_args.kwargs["params"]

    assert params["payment_behavior"] == "allow_incomplete"


# VALIDATION TESTS

@pytest.mark.parametrize(
    "customer_id",
    ["", " ", None, 123]
)
def test_create_subscription_invalid_customer_id(
        subscription_service,
        customer_id
):
    with pytest.raises(ValueError, match="Customer ID cannot be empty"):
        subscription_service.create_subscription(
            customer_id=customer_id,
            price_id="price_12345"
        )


@pytest.mark.parametrize(
    "price_id",
    ["", " ", None, 123]
)
def test_create_subscription_invalid_price_id(
        subscription_service,
        price_id
):
    with pytest.raises(ValueError, match="Price ID cannot be empty"):
        subscription_service.create_subscription(
            customer_id="cus_12345",
            price_id=price_id
        )


@pytest.mark.parametrize(
    "quantity",
    [0, -1, 1.5, True, "2"]
)
def test_create_subscription_invalid_quantity(
        subscription_service,
        quantity
):
    with pytest.raises(ValueError, match="Quantity must be a positive integer"):
        subscription_service.create_subscription(
            customer_id="cus_12345",
            price_id="price_12345",
            quantity=quantity
        )


def test_create_subscription_invalid_payment_behavior(
        subscription_service
):
    with pytest.raises(ValueError, match="Invalid payment behavior"):
        subscription_service.create_subscription(
            customer_id="cus_12345",
            price_id="price_12345",
            payment_behavior="invalid_behavior"
        )


def test_create_subscription_invalid_metadata(
        subscription_service
):
    with pytest.raises(ValueError, match="Metadata must be a dictionary"):
        subscription_service.create_subscription(
            customer_id="cus_12345",
            price_id="price_12345",
            metadata="invalid"
        )


def test_create_subscription_invalid_idempotency_key(
        subscription_service
):
    with pytest.raises(ValueError, match="Idempotency key cannot be empty"):
        subscription_service.create_subscription(
            customer_id="cus_12345",
            price_id="price_12345",
            idempotency_key=" "
        )


# RETRIEVE SUBSCRIPTION TESTS

def test_retrieve_subscription_success(
        subscription_service,
        mock_client
):
    mock_response = MagicMock()
    mock_client.v1.subscriptions.retrieve.return_value = mock_response

    result = subscription_service.retrieve_subscription("sub_12345")

    assert result == mock_response

    mock_client.v1.subscriptions.retrieve.assert_called_once_with(
        "sub_12345"
    )


@pytest.mark.parametrize(
    "subscription_id",
    ["", " ", None, 123]
)
def test_retrieve_subscription_invalid_id(
        subscription_service,
        subscription_id
):
    with pytest.raises(
            ValueError,
            match="Subscription ID cannot be empty"
    ):
        subscription_service.retrieve_subscription(subscription_id)


# UPDATE SUBSCRIPTION TESTS

def test_update_subscription_metadata_success(
        subscription_service,
        mock_client
):
    mock_response = MagicMock()
    mock_client.v1.subscriptions.update.return_value = mock_response

    metadata = {"plan": "premium"}

    result = subscription_service.update_subscription(
        subscription_id="sub_12345",
        metadata=metadata
    )

    assert result == mock_response

    mock_client.v1.subscriptions.update.assert_called_once_with(
        "sub_12345",
        params={"metadata": metadata},
        options={}
    )


def test_update_subscription_price_success(
        subscription_service,
        mock_client
):
    subscription_service.update_subscription(
        subscription_id="sub_12345",
        price_id="price_new123",
        subscription_item_id="si_12345"
    )

    params = mock_client.v1.subscriptions.update.call_args.kwargs["params"]

    assert params["items"] == [
        {
            "id": "si_12345",
            "price": "price_new123"
        }
    ]


def test_update_subscription_quantity_success(
        subscription_service,
        mock_client
):
    subscription_service.update_subscription(
        subscription_id="sub_12345",
        subscription_item_id="si_12345",
        quantity=3
    )

    params = mock_client.v1.subscriptions.update.call_args.kwargs["params"]

    assert params["items"][0]["quantity"] == 3


def test_update_subscription_with_idempotency_key(
        subscription_service,
        mock_client
):
    subscription_service.update_subscription(
        subscription_id="sub_12345",
        metadata={"plan": "premium"},
        idempotency_key="update_subscription_123"
    )

    options = mock_client.v1.subscriptions.update.call_args.kwargs["options"]

    assert options["idempotency_key"] == "update_subscription_123"


def test_update_subscription_invalid_id(
        subscription_service
):
    with pytest.raises(ValueError, match="Subscription ID cannot be empty"):
        subscription_service.update_subscription(
            subscription_id=" "
        )


def test_update_subscription_invalid_metadata(
        subscription_service
):
    with pytest.raises(ValueError, match="Metadata must be a dictionary"):
        subscription_service.update_subscription(
            subscription_id="sub_12345",
            metadata="invalid"
        )


def test_update_subscription_price_without_item_id(
        subscription_service
):
    with pytest.raises(ValueError, match="Subscription item ID is required"):
        subscription_service.update_subscription(
            subscription_id="sub_12345",
            price_id="price_new123"
        )


def test_update_subscription_quantity_without_item_id(
        subscription_service
):
    with pytest.raises(ValueError, match="Subscription item ID is required"):
        subscription_service.update_subscription(
            subscription_id="sub_12345",
            quantity=2
        )


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True, "2"])
def test_update_subscription_invalid_quantity(
        subscription_service,
        quantity
):
    with pytest.raises(ValueError, match="Quantity must be a positive integer"):
        subscription_service.update_subscription(
            subscription_id="sub_12345",
            subscription_item_id="si_12345",
            quantity=quantity
        )


def test_update_subscription_without_parameters(subscription_service):
    with pytest.raises(
        ValueError,
        match="Provide metadata, price ID, quantity, or proration behavior to update"
    ):
        subscription_service.update_subscription(
            subscription_id="sub_12345"
        )


# CANCEL SUBSCRIPTION TESTS

def test_cancel_subscription_immediately(
        subscription_service,
        mock_client
):
    mock_response = MagicMock()
    mock_client.v1.subscriptions.cancel.return_value = mock_response

    result = subscription_service.cancel_subscription(
        subscription_id="sub_12345"
    )

    assert result == mock_response

    mock_client.v1.subscriptions.cancel.assert_called_once_with(
        "sub_12345",
        params={},
        options={}
    )


def test_cancel_subscription_at_period_end(
        subscription_service,
        mock_client
):
    mock_response = MagicMock()
    mock_client.v1.subscriptions.update.return_value = mock_response

    result = subscription_service.cancel_subscription(
        subscription_id="sub_12345",
        cancel_at_period_end=True
    )

    assert result == mock_response

    mock_client.v1.subscriptions.update.assert_called_once_with(
        "sub_12345",
        params={"cancel_at_period_end": True},
        options={}
    )


def test_cancel_subscription_with_idempotency_key(
        subscription_service,
        mock_client
):
    subscription_service.cancel_subscription(
        subscription_id="sub_12345",
        idempotency_key="cancel_subscription_123"
    )

    options = mock_client.v1.subscriptions.cancel.call_args.kwargs["options"]

    assert options["idempotency_key"] == "cancel_subscription_123"


def test_cancel_subscription_invalid_id(
        subscription_service
):
    with pytest.raises(ValueError, match="Subscription ID cannot be empty"):
        subscription_service.cancel_subscription(
            subscription_id=" "
        )


@pytest.mark.parametrize(
    "cancel_at_period_end",
    ["true", 1, None]
)
def test_cancel_subscription_invalid_period_end(
        subscription_service,
        cancel_at_period_end
):
    with pytest.raises(
            ValueError,
            match="Cancel at period end must be a boolean"
    ):
        subscription_service.cancel_subscription(
            subscription_id="sub_12345",
            cancel_at_period_end=cancel_at_period_end
        )


def test_cancel_subscription_invalid_idempotency_key(
        subscription_service
):
    with pytest.raises(ValueError, match="Idempotency key cannot be empty"):
        subscription_service.cancel_subscription(
            subscription_id="sub_12345",
            idempotency_key=" "
        )


# LIST SUBSCRIPTIONS TESTS

def test_list_subscriptions_success(
    subscription_service,
    mock_client
):
    mock_response = MagicMock()
    mock_client.v1.subscriptions.list.return_value = mock_response

    result = subscription_service.list_subscriptions()

    assert result == mock_response

    mock_client.v1.subscriptions.list.assert_called_once_with(
        params={"limit": 10}
    )


def test_list_subscriptions_with_filters(
    subscription_service,
    mock_client
):
    subscription_service.list_subscriptions(
        limit=20,
        starting_after="sub_12345",
        customer_id="cus_12345",
        status="active"
    )

    params = mock_client.v1.subscriptions.list.call_args.kwargs["params"]

    assert params == {
        "limit": 20,
        "starting_after": "sub_12345",
        "customer": "cus_12345",
        "status": "active"
    }


def test_list_subscriptions_with_all_status(
    subscription_service,
    mock_client
):
    subscription_service.list_subscriptions(status="all")

    params = mock_client.v1.subscriptions.list.call_args.kwargs["params"]

    assert params["status"] == "all"


@pytest.mark.parametrize(
    "limit",
    [0, -1, 101, True, 1.5]
)
def test_list_subscriptions_invalid_limit(
    subscription_service,
    limit
):
    with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
        subscription_service.list_subscriptions(limit=limit)


@pytest.mark.parametrize(
    "starting_after",
    ["", " ", 123]
)
def test_list_subscriptions_invalid_starting_after(
    subscription_service,
    starting_after
):
    with pytest.raises(ValueError, match="Starting after cannot be empty"):
        subscription_service.list_subscriptions(
            starting_after=starting_after
        )


@pytest.mark.parametrize(
    "customer_id",
    ["", " ", 123]
)
def test_list_subscriptions_invalid_customer_id(
    subscription_service,
    customer_id
):
    with pytest.raises(ValueError, match="Customer ID cannot be empty"):
        subscription_service.list_subscriptions(
            customer_id=customer_id
        )


@pytest.mark.parametrize(
    "status",
    ["invalid", "unknown", 123]
)
def test_list_subscriptions_invalid_status(
    subscription_service,
    status
):
    with pytest.raises(ValueError, match="Invalid subscription status"):
        subscription_service.list_subscriptions(status=status)


# RESUME SUBSCRIPTION TESTS

def test_resume_subscription_success(
    subscription_service,
    mock_client
):
    mock_response = MagicMock()
    mock_client.v1.subscriptions.resume.return_value = mock_response

    result = subscription_service.resume_subscription("sub_12345")

    assert result == mock_response

    mock_client.v1.subscriptions.resume.assert_called_once_with(
        "sub_12345",
        params={},
        options={}
    )


def test_resume_subscription_with_idempotency_key(
    subscription_service,
    mock_client
):
    subscription_service.resume_subscription(
        "sub_12345",
        idempotency_key="resume_123"
    )

    options = mock_client.v1.subscriptions.resume.call_args.kwargs["options"]

    assert options["idempotency_key"] == "resume_123"


def test_resume_subscription_invalid_id(
    subscription_service
):
    with pytest.raises(ValueError, match="Subscription ID cannot be empty"):
        subscription_service.resume_subscription(" ")


def test_resume_collection_success(
    subscription_service,
    mock_client
):
    mock_response = MagicMock()
    mock_client.v1.subscriptions.update.return_value = mock_response

    result = subscription_service.resume_collection("sub_12345")

    assert result == mock_response

    mock_client.v1.subscriptions.update.assert_called_once_with(
        "sub_12345",
        params={"pause_collection": None},
        options={}
    )


def test_resume_collection_with_idempotency_key(
    subscription_service,
    mock_client
):
    subscription_service.resume_collection(
        "sub_12345",
        idempotency_key="resume_collection_123"
    )

    options = mock_client.v1.subscriptions.update.call_args.kwargs["options"]

    assert options["idempotency_key"] == "resume_collection_123"

# PAUSE COLLECTION TESTS

def test_pause_collection_success(
    subscription_service,
    mock_client
):
    mock_response = MagicMock()
    mock_client.v1.subscriptions.update.return_value = mock_response

    result = subscription_service.pause_collection("sub_12345")

    assert result == mock_response

    mock_client.v1.subscriptions.update.assert_called_once_with(
        "sub_12345",
        params={
            "pause_collection": {
                "behavior": "keep_as_draft"
            }
        },
        options={}
    )


@pytest.mark.parametrize(
    "behavior",
    ["keep_as_draft", "mark_uncollectible", "void"]
)
def test_pause_collection_with_different_behaviors(
    subscription_service,
    mock_client,
    behavior
):
    subscription_service.pause_collection(
        "sub_12345",
        behavior=behavior
    )

    params = mock_client.v1.subscriptions.update.call_args.kwargs["params"]

    assert params["pause_collection"]["behavior"] == behavior


def test_pause_collection_with_idempotency_key(
    subscription_service,
    mock_client
):
    subscription_service.pause_collection(
        "sub_12345",
        idempotency_key="pause_collection_123"
    )

    options = mock_client.v1.subscriptions.update.call_args.kwargs["options"]

    assert options["idempotency_key"] == "pause_collection_123"


def test_pause_collection_invalid_subscription_id(
    subscription_service
):
    with pytest.raises(ValueError, match="Subscription ID cannot be empty"):
        subscription_service.pause_collection(" ")


@pytest.mark.parametrize(
    "behavior",
    ["invalid", "", None, 123]
)
def test_pause_collection_invalid_behavior(
    subscription_service,
    behavior
):
    with pytest.raises(ValueError, match="Invalid pause collection behavior"):
        subscription_service.pause_collection(
            "sub_12345",
            behavior=behavior
        )


def test_pause_collection_invalid_idempotency_key(
    subscription_service
):
    with pytest.raises(ValueError, match="Idempotency key cannot be empty"):
        subscription_service.pause_collection(
            "sub_12345",
            idempotency_key=" "
        )

@pytest.mark.parametrize(
    "behavior",
    ["create_prorations", "none", "always_invoice"]
)
def test_update_subscription_proration_behavior(
    subscription_service,
    mock_client,
    behavior
):
    subscription_service.update_subscription(
        subscription_id="sub_12345",
        metadata={"plan": "premium"},
        proration_behavior=behavior
    )

    params = mock_client.v1.subscriptions.update.call_args.kwargs["params"]

    assert params["proration_behavior"] == behavior


def test_update_subscription_invalid_proration_behavior(
    subscription_service
):
    with pytest.raises(
        ValueError,
        match="Invalid proration behavior"
    ):
        subscription_service.update_subscription(
            subscription_id="sub_12345",
            metadata={"plan": "premium"},
            proration_behavior="invalid"
        )


import json
import time
from unittest.mock import Mock

import pytest
import stripe

from app.src.stripe_services.webhooks.webhook_service import (
    WebhookService,
)


@pytest.fixture
def webhook_secret():
    return "whsec_test_secret"


@pytest.fixture
def event_repository():
    repository = Mock()
    repository.claim_event.return_value = True
    repository.mark_processed.return_value = True
    repository.mark_failed.return_value = True
    return repository


@pytest.fixture
def webhook_service(webhook_secret, event_repository):
    return WebhookService(
        webhook_secret=webhook_secret,
        event_repository=event_repository,
    )


@pytest.fixture
def webhook_payload():
    return json.dumps({
        "id": "evt_test_123",
        "object": "event",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_123",
                "object": "payment_intent",
                "amount": 2000,
                "currency": "usd",
            }
        },
    })


@pytest.fixture
def signature_header(webhook_payload, webhook_secret):
    return stripe.WebhookSignature.generate_signature_header(
        webhook_payload,
        webhook_secret,
        int(time.time()),
    )


@pytest.fixture
def stripe_event(webhook_payload):
    return stripe.Event.construct_from(
        json.loads(webhook_payload),
        stripe.api_key,
    )


# ---------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------

def test_initialize_webhook_service(
    webhook_secret,
    event_repository,
):
    service = WebhookService(
        webhook_secret=webhook_secret,
        event_repository=event_repository,
    )

    assert service.webhook_secret == webhook_secret
    assert service.event_repository is event_repository


def test_initialize_with_empty_secret(event_repository):
    service = WebhookService(
        webhook_secret="",
        event_repository=event_repository,
    )

    assert service.webhook_secret == ""


# ---------------------------------------------------------
# Signature verification tests
# ---------------------------------------------------------

def test_verify_valid_webhook_signature(
    webhook_service,
    webhook_payload,
    signature_header,
):
    event = webhook_service.verify_event(
        payload=webhook_payload,
        sig_header=signature_header,
    )

    assert isinstance(event, stripe.Event)
    assert event.id == "evt_test_123"
    assert event.type == "payment_intent.succeeded"


def test_verify_webhook_with_bytes_payload(
    webhook_service,
    webhook_payload,
    webhook_secret,
):
    payload = webhook_payload.encode("utf-8")

    signature = stripe.WebhookSignature.generate_signature_header(
        webhook_payload,
        webhook_secret,
        int(time.time()),
    )

    event = webhook_service.verify_event(
        payload=payload,
        sig_header=signature,
    )

    assert event.id == "evt_test_123"


def test_verify_webhook_with_invalid_signature(
    webhook_service,
    webhook_payload,
):
    with pytest.raises(stripe.SignatureVerificationError):
        webhook_service.verify_event(
            payload=webhook_payload,
            sig_header="invalid_signature",
        )


def test_verify_webhook_with_invalid_payload(
    webhook_service,
    webhook_secret,
):
    payload = "invalid JSON"

    signature = stripe.WebhookSignature.generate_signature_header(
        payload,
        webhook_secret,
        int(time.time()),
    )

    with pytest.raises(ValueError):
        webhook_service.verify_event(
            payload=payload,
            sig_header=signature,
        )


def test_verify_webhook_with_empty_payload(webhook_service):
    with pytest.raises(
        ValueError,
        match="Webhook payload cannot be empty",
    ):
        webhook_service.verify_event(
            payload="",
            sig_header="signature",
        )


def test_verify_webhook_with_missing_signature(
    webhook_service,
    webhook_payload,
):
    with pytest.raises(
        ValueError,
        match="Stripe signature header is required",
    ):
        webhook_service.verify_event(
            payload=webhook_payload,
            sig_header="",
        )


def test_verify_webhook_with_missing_secret(
    webhook_payload,
    signature_header,
    event_repository,
):
    service = WebhookService(
        webhook_secret=None,
        event_repository=event_repository,
    )
    service.webhook_secret = None

    with pytest.raises(
        ValueError,
        match="Stripe webhook secret is not configured",
    ):
        service.verify_event(
            payload=webhook_payload,
            sig_header=signature_header,
        )


def test_verify_webhook_with_invalid_payload_type(webhook_service):
    with pytest.raises(
        ValueError,
        match="Webhook payload must be bytes or string",
    ):
        webhook_service.verify_event(
            payload=12345,
            sig_header="signature",
        )


# ---------------------------------------------------------
# Event extraction tests
# ---------------------------------------------------------

def test_get_event_id(webhook_service, stripe_event):
    assert webhook_service.get_event_id(stripe_event) == "evt_test_123"


def test_get_event_type(webhook_service, stripe_event):
    assert (
        webhook_service.get_event_type(stripe_event)
        == "payment_intent.succeeded"
    )


def test_get_event_object(webhook_service, stripe_event):
    event_object = webhook_service.get_event_object(stripe_event)

    assert event_object.id == "pi_test_123"
    assert event_object.amount == 2000


def test_get_event_id_missing(webhook_service):
    event = {"type": "payment_intent.succeeded"}

    with pytest.raises(ValueError, match="Stripe event ID is missing"):
        webhook_service.get_event_id(event)


def test_get_event_type_missing(webhook_service):
    event = {"id": "evt_test_123"}

    with pytest.raises(ValueError, match="Stripe event type is missing"):
        webhook_service.get_event_type(event)


def test_get_event_data_missing(webhook_service):
    event = {
        "id": "evt_test_123",
        "type": "payment_intent.succeeded",
    }

    with pytest.raises(ValueError, match="Stripe event data is missing"):
        webhook_service.get_event_object(event)


# ---------------------------------------------------------
# Event dispatch tests
# ---------------------------------------------------------

def test_dispatch_registered_event(webhook_service, stripe_event):
    handler = Mock(return_value="processed")

    handlers = {
        "payment_intent.succeeded": handler,
    }

    result = webhook_service.dispatch_event(
        event=stripe_event,
        handlers=handlers,
    )

    handler.assert_called_once_with(stripe_event)
    assert result == "processed"


def test_dispatch_unsupported_event(webhook_service, stripe_event):
    handlers = {
        "invoice.paid": Mock(),
    }

    result = webhook_service.dispatch_event(
        event=stripe_event,
        handlers=handlers,
    )

    assert result is None


def test_dispatch_invalid_handlers(webhook_service, stripe_event):
    with pytest.raises(ValueError, match="Handlers must be a mapping"):
        webhook_service.dispatch_event(
            event=stripe_event,
            handlers=None,
        )


def test_dispatch_non_callable_handler(webhook_service, stripe_event):
    handlers = {
        "payment_intent.succeeded": "not_callable",
    }

    with pytest.raises(ValueError, match="must be callable"):
        webhook_service.dispatch_event(
            event=stripe_event,
            handlers=handlers,
        )


# ---------------------------------------------------------
# End-to-end processing tests
# ---------------------------------------------------------

def test_process_event_success(
    webhook_service,
    webhook_payload,
    signature_header,
    event_repository,
):
    handler = Mock(return_value="payment processed")

    handlers = {
        "payment_intent.succeeded": handler,
    }

    result = webhook_service.process_event(
        payload=webhook_payload,
        sig_header=signature_header,
        handlers=handlers,
    )

    assert result == "payment processed"

    processed_event = handler.call_args.args[0]

    assert processed_event.id == "evt_test_123"
    assert processed_event.type == "payment_intent.succeeded"

    event_repository.claim_event.assert_called_once_with(
        stripe_event_id="evt_test_123",
        event_type="payment_intent.succeeded",
    )
    event_repository.mark_processed.assert_called_once_with(
        "evt_test_123"
    )
    event_repository.mark_failed.assert_not_called()


def test_process_event_invalid_signature(
    webhook_service,
    webhook_payload,
    event_repository,
):
    handler = Mock()

    with pytest.raises(stripe.SignatureVerificationError):
        webhook_service.process_event(
            payload=webhook_payload,
            sig_header="invalid_signature",
            handlers={
                "payment_intent.succeeded": handler,
            },
        )

    handler.assert_not_called()
    event_repository.claim_event.assert_not_called()


def test_process_event_duplicate(
    webhook_service,
    webhook_payload,
    signature_header,
    event_repository,
):
    event_repository.claim_event.return_value = False

    handler = Mock()

    result = webhook_service.process_event(
        payload=webhook_payload,
        sig_header=signature_header,
        handlers={
            "payment_intent.succeeded": handler,
        },
    )

    assert result is None

    handler.assert_not_called()
    event_repository.mark_processed.assert_not_called()
    event_repository.mark_failed.assert_not_called()


def test_process_event_handler_failure(
    webhook_service,
    webhook_payload,
    signature_header,
    event_repository,
):
    handler = Mock(side_effect=RuntimeError("Payment handler failed"))

    with pytest.raises(
        RuntimeError,
        match="Payment handler failed",
    ):
        webhook_service.process_event(
            payload=webhook_payload,
            sig_header=signature_header,
            handlers={
                "payment_intent.succeeded": handler,
            },
        )

    handler.assert_called_once()

    event_repository.mark_failed.assert_called_once_with(
        stripe_event_id="evt_test_123",
        error_message="Payment handler failed",
    )

    event_repository.mark_processed.assert_not_called()


def test_process_event_mark_processed_failure(
    webhook_service,
    webhook_payload,
    signature_header,
    event_repository,
):
    event_repository.mark_processed.return_value = False

    handler = Mock(return_value="payment processed")

    with pytest.raises(
        RuntimeError,
        match="Could not mark Stripe event evt_test_123 as processed",
    ):
        webhook_service.process_event(
            payload=webhook_payload,
            sig_header=signature_header,
            handlers={
                "payment_intent.succeeded": handler,
            },
        )

    handler.assert_called_once()


def test_process_event_unsupported_type(
    webhook_service,
    webhook_payload,
    signature_header,
    event_repository,
):
    handlers = {
        "invoice.paid": Mock(),
    }

    result = webhook_service.process_event(
        payload=webhook_payload,
        sig_header=signature_header,
        handlers=handlers,
    )

    assert result is None

    event_repository.claim_event.assert_called_once()
    event_repository.mark_processed.assert_called_once_with(
        "evt_test_123"
    )


import json
import time
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from stripe import WebhookSignature

from app.src.main import app
from app.src.api import webhook_routes


client = TestClient(app)

TEST_SECRET = "whsec_route_test_secret"


@pytest.fixture
def event_repository():
    repository = Mock()
    repository.claim_event.return_value = True
    repository.mark_processed.return_value = True
    repository.mark_failed.return_value = True
    return repository


@pytest.fixture
def setup_webhook(event_repository, monkeypatch):
    from app.src.stripe_services.webhooks.webhook_service import (
        WebhookService,
    )

    service = WebhookService(
        webhook_secret=TEST_SECRET,
        event_repository=event_repository,
    )

    monkeypatch.setattr(
        webhook_routes,
        "webhook_service",
        service,
    )

    return event_repository


@pytest.fixture
def webhook_payload():
    return json.dumps({
        "id": "evt_route_test_123",
        "object": "event",
        "type": "invoice.paid",
        "data": {
            "object": {
                "id": "in_test_123",
                "object": "invoice",
            }
        },
    })


def generate_signature(payload):
    return WebhookSignature.generate_signature_header(
        payload,
        TEST_SECRET,
        int(time.time()),
    )


def test_webhook_missing_signature(webhook_payload):
    response = client.post(
        "/webhook",
        content=webhook_payload,
    )

    assert response.status_code == 422


def test_webhook_invalid_signature(
    setup_webhook,
    webhook_payload,
):
    response = client.post(
        "/webhook",
        content=webhook_payload,
        headers={
            "Stripe-Signature": "invalid_signature",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid Stripe webhook signature"
    )

    setup_webhook.claim_event.assert_not_called()


def test_webhook_success(
    setup_webhook,
    webhook_payload,
):
    signature = generate_signature(webhook_payload)

    response = client.post(
        "/webhook",
        content=webhook_payload,
        headers={
            "Stripe-Signature": signature,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    setup_webhook.claim_event.assert_called_once_with(
        stripe_event_id="evt_route_test_123",
        event_type="invoice.paid",
    )

    setup_webhook.mark_processed.assert_called_once_with(
        "evt_route_test_123"
    )


def test_webhook_duplicate_event(
    setup_webhook,
    webhook_payload,
):
    setup_webhook.claim_event.return_value = False

    signature = generate_signature(webhook_payload)

    response = client.post(
        "/webhook",
        content=webhook_payload,
        headers={
            "Stripe-Signature": signature,
        },
    )

    assert response.status_code == 200

    setup_webhook.mark_processed.assert_not_called()
    setup_webhook.mark_failed.assert_not_called()


def test_webhook_processing_failure(
    setup_webhook,
    webhook_payload,
):
    setup_webhook.claim_event.return_value = True
    setup_webhook.mark_processed.return_value = False

    signature = generate_signature(webhook_payload)

    response = client.post(
        "/webhook",
        content=webhook_payload,
        headers={
            "Stripe-Signature": signature,
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Webhook processing failed"
    )

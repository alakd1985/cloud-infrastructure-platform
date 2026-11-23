
from uuid import uuid4

import pytest
from sqlalchemy import delete

from app.src.database.database import SessionLocal
from app.src.database.models.webhook_event import WebhookEvent
from app.src.database.repositories.webhook_event_repository import (
    WebhookEventRepository,
)


@pytest.fixture
def repository():
    return WebhookEventRepository()


@pytest.fixture
def event_id():
    """Generate a unique Stripe event ID for each test."""
    return f"evt_test_{uuid4().hex}"


@pytest.fixture
def cleanup_event(event_id):
    """Remove the test event after the test finishes."""
    yield event_id

    with SessionLocal.begin() as session:
        session.execute(
            delete(WebhookEvent).where(
                WebhookEvent.stripe_event_id == event_id
            )
        )


def test_claim_new_event(repository, cleanup_event):
    claimed = repository.claim_event(
        cleanup_event,
        "payment_intent.succeeded",
    )

    assert claimed is True

    event = repository.get_event(cleanup_event)

    assert event is not None
    assert event.status == "processing"
    assert event.event_type == "payment_intent.succeeded"
    assert event.processed_at is None


def test_prevent_duplicate_event_claim(repository, cleanup_event):
    first_claim = repository.claim_event(
        cleanup_event,
        "payment_intent.succeeded",
    )

    second_claim = repository.claim_event(
        cleanup_event,
        "payment_intent.succeeded",
    )

    assert first_claim is True
    assert second_claim is False


def test_mark_event_processed(repository, cleanup_event):
    repository.claim_event(
        cleanup_event,
        "payment_intent.succeeded",
    )

    updated = repository.mark_processed(cleanup_event)

    assert updated is True

    event = repository.get_event(cleanup_event)

    assert event.status == "processed"
    assert event.processed_at is not None
    assert event.error_message is None


def test_mark_event_failed(repository, cleanup_event):
    repository.claim_event(
        cleanup_event,
        "payment_intent.payment_failed",
    )

    updated = repository.mark_failed(
        cleanup_event,
        "Payment processing failed",
    )

    assert updated is True

    event = repository.get_event(cleanup_event)

    assert event.status == "failed"
    assert event.error_message == "Payment processing failed"


def test_retry_failed_event(repository, cleanup_event):
    repository.claim_event(
        cleanup_event,
        "payment_intent.payment_failed",
    )

    repository.mark_failed(
        cleanup_event,
        "Temporary payment failure",
    )

    retry_claimed = repository.claim_event(
        cleanup_event,
        "payment_intent.payment_failed",
    )

    assert retry_claimed is True

    event = repository.get_event(cleanup_event)

    assert event.status == "processing"
    assert event.error_message is None
    assert event.processed_at is None


def test_get_nonexistent_event(repository):
    event = repository.get_event(
        f"evt_missing_{uuid4().hex}"
    )

    assert event is None


def test_cannot_mark_already_processed_event_failed(
    repository,
    cleanup_event,
):
    repository.claim_event(
        cleanup_event,
        "payment_intent.succeeded",
    )

    repository.mark_processed(cleanup_event)

    updated = repository.mark_failed(
        cleanup_event,
        "This should not overwrite a processed event",
    )

    assert updated is False

    event = repository.get_event(cleanup_event)

    assert event.status == "processed"
    assert event.error_message is None

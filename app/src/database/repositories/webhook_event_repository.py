
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker

from app.src.database.database import SessionLocal
from app.src.database.models.webhook_event import WebhookEvent


class WebhookEventRepository:
    """
    Handles persistent Stripe webhook event storage.

    PostgreSQL's ON CONFLICT operation provides atomic event claiming,
    preventing concurrent requests from claiming the same event.
    """

    def __init__(
        self,
        session_factory: sessionmaker = SessionLocal,
    ):
        self.session_factory = session_factory

    def claim_event(
        self,
        stripe_event_id: str,
        event_type: str,
    ) -> bool:
        """
        Claim a new event or retry a previously failed event.

        Returns:
            True: Event successfully claimed.
            False: Event is already processing or processed.
        """

        statement = (
            insert(WebhookEvent)
            .values(
                stripe_event_id=stripe_event_id,
                event_type=event_type,
                status="processing",
            )
            .on_conflict_do_update(
                index_elements=[WebhookEvent.stripe_event_id],
                set_={
                    "status": "processing",
                    "error_message": None,
                    "processed_at": None,
                },
                where=WebhookEvent.status == "failed",
            )
            .returning(WebhookEvent.id)
        )

        with self.session_factory.begin() as session:
            result = session.execute(statement)
            claimed_id = result.scalar_one_or_none()

        return claimed_id is not None

    def mark_processed(self, stripe_event_id: str) -> bool:
        """Mark a successfully processed event."""

        statement = (
            update(WebhookEvent)
            .where(
                WebhookEvent.stripe_event_id == stripe_event_id,
                WebhookEvent.status == "processing",
            )
            .values(
                status="processed",
                processed_at=datetime.now(timezone.utc),
                error_message=None,
            )
        )

        with self.session_factory.begin() as session:
            result = session.execute(statement)

        return result.rowcount == 1

    def mark_failed(
        self,
        stripe_event_id: str,
        error_message: str,
    ) -> bool:
        """Record a processing failure."""

        statement = (
            update(WebhookEvent)
            .where(
                WebhookEvent.stripe_event_id == stripe_event_id,
                WebhookEvent.status == "processing",
            )
            .values(
                status="failed",
                error_message=error_message[:2000],
            )
        )

        with self.session_factory.begin() as session:
            result = session.execute(statement)

        return result.rowcount == 1

    def get_event(
        self,
        stripe_event_id: str,
    ) -> Optional[WebhookEvent]:
        """Retrieve a webhook event by its Stripe event ID."""

        statement = select(WebhookEvent).where(
            WebhookEvent.stripe_event_id == stripe_event_id
        )

        with self.session_factory() as session:
            return session.execute(statement).scalar_one_or_none()

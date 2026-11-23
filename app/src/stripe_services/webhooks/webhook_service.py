
from typing import Any, Callable, Mapping, Optional, Union

import stripe

from app.src.config import STRIPE_WEBHOOK_SECRET
from app.src.database.repositories.webhook_event_repository import (
    WebhookEventRepository,
)


WebhookPayload = Union[str, bytes, bytearray]
EventHandler = Callable[[Any], Any]


class WebhookService:
    """
    Verifies Stripe webhook signatures, tracks event processing
    in PostgreSQL, and dispatches verified events.
    """

    def __init__(
        self,
        webhook_secret: Optional[str] = None,
        event_repository: Optional[WebhookEventRepository] = None,
    ):
        self.webhook_secret = (
            webhook_secret
            if webhook_secret is not None
            else STRIPE_WEBHOOK_SECRET
        )

        self.event_repository = (
            event_repository
            if event_repository is not None
            else WebhookEventRepository()
        )

    @staticmethod
    def _get_field(obj: Any, key: str) -> Any:
        """Read a field from either a dictionary or Stripe object."""

        if isinstance(obj, Mapping):
            return obj.get(key)

        try:
            return obj[key]
        except (KeyError, TypeError, AttributeError):
            return getattr(obj, key, None)

    def verify_event(
        self,
        payload: WebhookPayload,
        sig_header: str,
    ) -> stripe.Event:

        if not isinstance(payload, (str, bytes, bytearray)):
            raise ValueError(
                "Webhook payload must be bytes or string"
            )

        if not payload:
            raise ValueError("Webhook payload cannot be empty")

        if not isinstance(sig_header, str) or not sig_header.strip():
            raise ValueError("Stripe signature header is required")

        if (
            not isinstance(self.webhook_secret, str)
            or not self.webhook_secret.strip()
        ):
            raise ValueError(
                "Stripe webhook secret is not configured"
            )

        return stripe.Webhook.construct_event(
            payload,
            sig_header,
            self.webhook_secret,
        )

    def get_event_id(self, event: Any) -> str:
        event_id = self._get_field(event, "id")

        if not event_id:
            raise ValueError("Stripe event ID is missing")

        return event_id

    def get_event_type(self, event: Any) -> str:
        event_type = self._get_field(event, "type")

        if not event_type:
            raise ValueError("Stripe event type is missing")

        return event_type

    def get_event_object(self, event: Any) -> Any:
        data = self._get_field(event, "data")

        if data is None:
            raise ValueError("Stripe event data is missing")

        event_object = self._get_field(data, "object")

        if event_object is None:
            raise ValueError(
                "Stripe event data object is missing"
            )

        return event_object

    def dispatch_event(
        self,
        event: Any,
        handlers: Mapping[str, EventHandler],
    ) -> Any:

        if not isinstance(handlers, Mapping):
            raise ValueError("Handlers must be a mapping")

        event_type = self.get_event_type(event)
        handler = handlers.get(event_type)

        if handler is None:
            return None

        if not callable(handler):
            raise ValueError(
                f"Handler for {event_type} must be callable"
            )

        return handler(event)

    def process_event(
        self,
        payload: WebhookPayload,
        sig_header: str,
        handlers: Mapping[str, EventHandler],
    ) -> Any:
        """
        Verify, claim, dispatch, and persist a Stripe webhook event.

        Duplicate or currently processing events are skipped.
        Failed handlers are recorded and their exceptions re-raised.
        """

        # 1. Verify signature before database operations.
        event = self.verify_event(
            payload=payload,
            sig_header=sig_header,
        )

        # 2. Extract event metadata.
        event_id = self.get_event_id(event)
        event_type = self.get_event_type(event)

        # 3. Atomically claim the event in PostgreSQL.
        claimed = self.event_repository.claim_event(
            stripe_event_id=event_id,
            event_type=event_type,
        )

        if not claimed:
            # Already processing or successfully processed.
            return None

        # 4. Dispatch the event handler.
        try:
            result = self.dispatch_event(
                event=event,
                handlers=handlers,
            )

        except Exception as exc:
            # 5. Persist the failure, then allow Stripe to retry.
            self.event_repository.mark_failed(
                stripe_event_id=event_id,
                error_message=str(exc),
            )
            raise

        # 6. Persist successful processing.
        updated = self.event_repository.mark_processed(event_id)

        if not updated:
            raise RuntimeError(
                f"Could not mark Stripe event {event_id} as processed"
            )

        return result

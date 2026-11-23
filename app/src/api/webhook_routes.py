
import stripe

from fastapi import APIRouter, Header, HTTPException, Request

from app.src.stripe_services.webhooks.webhook_service import (
    WebhookService,
)


router = APIRouter()

webhook_service = WebhookService()

# Register actual event handlers here as we implement them.
WEBHOOK_HANDLERS = {}


@router.post("/webhook")
async def receive_stripe_webhook(
    request: Request,
    stripe_signature: str = Header(
        ...,
        alias="Stripe-Signature",
    ),
):
    """
    Receive and process Stripe webhook events.

    Stripe requires the original raw request body for signature
    verification. Do not parse the request as JSON first.
    """

    payload = await request.body()

    try:
        result = webhook_service.process_event(
            payload=payload,
            sig_header=stripe_signature,
            handlers=WEBHOOK_HANDLERS,
        )

        return {
            "status": "success",
            "message": "Webhook received and processed",
            "result": result,
        }

    except stripe.SignatureVerificationError:
        raise HTTPException(
            status_code=400,
            detail="Invalid Stripe webhook signature",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        # A 500 response tells Stripe that processing failed
        # and that it may retry delivery.
        raise HTTPException(
            status_code=500,
            detail="Webhook processing failed",
        )

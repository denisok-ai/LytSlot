"""
@file: webhooks.py
@description: Stripe and YooKassa webhooks -> Celery task to update payment.
@dependencies: fastapi, services.api.config
@created: 2025-02-19
"""

from fastapi import APIRouter, BackgroundTasks, Request, Response

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe", summary="Webhook Stripe")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    _body = await request.body()  # TODO: verify signature, process_webhook.delay("stripe", _body)
    return Response(status_code=200)


@router.post("/yookassa", summary="Webhook ЮKassa")
async def yookassa_webhook(request: Request, background_tasks: BackgroundTasks):
    _body = await request.json()  # TODO: verify signature, process_webhook.delay("yookassa", _body)
    return Response(status_code=200)

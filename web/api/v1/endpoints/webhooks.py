from fastapi import APIRouter, Request, HTTPException
from web.services.webhook_service import WebhookService
from web.core.websocket_manager import manager

router = APIRouter()


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        data = await request.json()
        webhook_service = WebhookService()

        # Processar webhook do WhatsApp
        result = await webhook_service.process_whatsapp_webhook(data)

        if result:
            # Notificar clientes via WebSocket
            await manager.broadcast(f"New message received: {result}")

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/whatsapp")
async def verify_webhook(
        hub_mode: str = None,
        hub_challenge: str = None,
        hub_verify_token: str = None
):
    # Verificação do webhook do WhatsApp
    if hub_mode == "subscribe" and hub_verify_token == "your_verify_token":
        return int(hub_challenge)
    return HTTPException(status_code=403, detail="Forbidden")
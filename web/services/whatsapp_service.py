import aiohttp
import qrcode
import io
import base64
from typing import Optional, Dict, Any
from web.core.config import settings
from web.models import MessageType


class WhatsAppService:
    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.token = settings.WHATSAPP_TOKEN

    async def generate_qr_code(self) -> str:
        """Gera QR Code para autenticação"""
        # Simulação - implementar integração real com WhatsApp Business API
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data("whatsapp://authenticate/session_token_here")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"

    async def send_message(
            self,
            chat_id: int,
            content: str,
            message_type: MessageType = MessageType.TEXT,
            media_url: Optional[str] = None
    ) -> bool:
        """Envia mensagem via WhatsApp"""
        try:
            # Implementar envio real via WhatsApp Business API
            async with aiohttp.ClientSession() as session:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": f"chat_{chat_id}",  # Substituir pelo número real
                    "type": message_type.value,
                }

                if message_type == MessageType.TEXT:
                    payload["text"] = {"body": content}
                elif message_type == MessageType.IMAGE:
                    payload["image"] = {"link": media_url, "caption": content}
                elif message_type == MessageType.AUDIO:
                    payload["audio"] = {"link": media_url}
                # Adicionar outros tipos conforme necessário

                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }

                async with session.post(
                        f"{self.api_url}/messages",
                        json=payload,
                        headers=headers
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            return False

    async def download_media(self, media_id: str) -> Optional[bytes]:
        """Baixa mídia do WhatsApp"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.token}"}
                async with session.get(
                        f"{self.api_url}/media/{media_id}",
                        headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.read()
        except Exception as e:
            print(f"Erro ao baixar mídia: {e}")
        return None
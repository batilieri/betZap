import requests
import json
import logging

# Configuração de logging para melhor depuração
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WhatsAppAPI:
    def __init__(self, instance_id, api_token, base_url="https://api.w-api.app/v1/"):
        """
        Inicializa a classe WhatsAppAPI para interagir com a API W-API do WhatsApp

        Args:
            instance_id (str): ID da instância do WhatsApp
            api_token (str): Token de autenticação da API
            base_url (str): URL base da API
        """
        self.instance_id = instance_id
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }

    def send_text_message(self, phone_number, message, delay_message=1):
        """
        Envia uma mensagem de texto para um contato via WhatsApp

        Args:
            phone_number (str): Número de telefone do destinatário (com código do país, sem símbolos)
            message (str): Mensagem a ser enviada
            delay_message (int, optional): Delay em segundos. Default: 1.

        Returns:
            dict: Resposta da API
        """
        url = f"{self.base_url}message/send-text?instanceId={self.instance_id}"

        payload = {
            "phone": phone_number,
            "message": message,
            "delayMessage": delay_message
        }

        try:
            logger.info(f"Enviando mensagem para {phone_number}")
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            try:
                result = response.json()
                logger.info(f"Mensagem enviada com sucesso: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON: {e}")
                logger.debug(f"Resposta: {response.text}")
                return {
                    "success": False,
                    "error": "Resposta não é um JSON válido",
                    "response_text": response.text
                }

        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP: {e}")
            return {"success": False, "error": f"Erro HTTP: {e}", "status_code": e.response.status_code}
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de requisição: {e}")
            return {"success": False, "error": f"Erro de requisição: {e}"}

    def check_connection_status(self, api_token=None, id_instance=None):
        """Verifica status da conexão W-API"""
        try:
            headers = {
                'Authorization': f'Bearer {api_token}'
            }

            # Instance ID é obrigatório
            if not id_instance:
                return 'error'

            params = {
                'instanceId': id_instance
            }

            response = requests.get(
                f"{self.base_url}/v1/instance/status-instance",
                headers=headers,
                params=params,
                timeout=1
            )

            # Verificar tipo de conteúdo
            content_type = response.headers.get('Content-Type', '')

            if response.status_code == 200:
                if 'application/json' in content_type:
                    try:
                        data = response.json()

                        if data.get("error"):
                            return 'error'

                        # Status possíveis da W-API: 'connected', 'disconnected', 'connecting'
                        status = data.get('status', 'waiting')
                        return status

                    except ValueError:
                        # Se não conseguir fazer parse do JSON
                        return 'error'
                else:
                    return 'error'
            else:
                return 'error'

        except requests.exceptions.Timeout as e:
            print(e)
            return 'error'
        except requests.RequestException as e:
            print(f"Erro de requisição: {e}")
            return 'error'
        except Exception as e:
            print(f"Erro inesperado: {e}")
            return 'error'

    def stop(self):
        """Para o thread"""
        self.running = False


# Exemplo de uso
if __name__ == "__main__":
    # Configurações da API - substitua pelos seus dados reais
    INSTANCE_ID = "LITE-YLOCZC-ZGHBVR"
    API_TOKEN = "1paGyOfRfDdQLg5nnWyXvVoa9XDCB8VWr"

    # Inicializa a API
    whatsapp_api = WhatsAppAPI(INSTANCE_ID, API_TOKEN)
    status = whatsapp_api.check_connection_status(api_token=API_TOKEN, id_instance=INSTANCE_ID)
    print(status)
    if status == "connected":
        PHONE_NUMBER = "5569999267344"
        MESSAGE = "Oi meu nenem fofinha."
        result = whatsapp_api.send_text_message(PHONE_NUMBER, MESSAGE)
        print("Resultado do envio:", result)
    else:
        PHONE_NUMBER = "5569999267344"
        MESSAGE = "Você é o amor de minha vidaaa!"

        # Envia a mensagem
        result = whatsapp_api.send_text_message(PHONE_NUMBER, MESSAGE, delay_message=1)
        print("Resultado do envio:", result)

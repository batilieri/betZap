import requests
import json
import base64
import os
import mimetypes
from urllib.parse import urlparse


class EnviaImagem:
    """Classe para enviar imagens locais via WhatsApp usando a API W-API."""

    def __init__(self, instance_id, api_token, base_url="https://api.w-api.app/v1/message"):
        """
        Inicializa a classe EnviaImagem.

        Args:
            instance_id (str): ID da instância do WhatsApp.
            api_token (str): Token de autenticação da API.
            base_url (str): URL base da API.
        """
        self.instance_id = instance_id
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }

    def enviar(self, phone_number, caminho_imagem, caption="", delay_message=1):
        """
        Envia imagem local via WhatsApp.
        Se for detectada uma URL, também funciona.

        Args:
            phone_number (str): Número de telefone do destinatário.
            caminho_imagem (str): Caminho local da imagem (ex: '/pasta/imagem.jpg').
            caption (str): Legenda da imagem (opcional).
            delay_message (int): Delay em segundos.

        Returns:
            dict: Resultado da operação com success, data/error, e detalhes.
        """
        # Valida o número de telefone
        if not self._validar_numero(phone_number):
            return {
                "success": False,
                "error": "Número de telefone inválido",
                "details": "O número deve ter pelo menos 10 dígitos"
            }

        # Detecta se por acaso foi passada uma URL (para compatibilidade)
        if self._is_url(caminho_imagem):
            return self._enviar_url(phone_number, caminho_imagem, caption, delay_message)

        # Processo principal: arquivo local
        return self._enviar_arquivo_local(phone_number, caminho_imagem, caption, delay_message)

    def _is_url(self, string):
        """Verifica se a string é uma URL válida."""
        try:
            result = urlparse(string)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _validar_numero(self, phone_number):
        """Valida se o número de telefone está no formato correto."""
        numero_limpo = ''.join(filter(str.isdigit, phone_number))

        if len(numero_limpo) < 10:
            return False

        # Para números brasileiros
        if numero_limpo.startswith('55') and len(numero_limpo) >= 12:
            return True

        return len(numero_limpo) >= 10

    def _enviar_arquivo_local(self, phone_number, caminho_imagem, caption, delay_message):
        """Processa e envia imagem local."""
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(caminho_imagem):
                return {
                    "success": False,
                    "error": f"Arquivo não encontrado: {caminho_imagem}",
                    "details": "Verifique se o caminho está correto"
                }

            # Verifica se é um arquivo de imagem
            if not self._is_imagem_valida(caminho_imagem):
                return {
                    "success": False,
                    "error": "Arquivo não é uma imagem válida",
                    "details": "Formatos suportados: jpg, jpeg, png, gif, webp"
                }

            # Converte para base64
            image_base64 = self._converter_para_base64(caminho_imagem)
            if not image_base64:
                return {
                    "success": False,
                    "error": "Erro ao converter imagem para base64"
                }

            # Prepara payload
            payload = {
                "phone": phone_number,
                "image": image_base64,
                "delayMessage": delay_message
            }

            if caption:
                payload["caption"] = caption

            return self._fazer_requisicao(payload)

        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao processar arquivo local: {str(e)}"
            }

    def _enviar_url(self, phone_number, image_url, caption, delay_message):
        """Envia URL diretamente (caso seja detectada)."""
        try:
            payload = {
                "phone": phone_number,
                "image": image_url,
                "delayMessage": delay_message
            }

            if caption:
                payload["caption"] = caption

            return self._fazer_requisicao(payload)

        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao enviar URL: {str(e)}"
            }

    def _is_imagem_valida(self, caminho_imagem):
        """Verifica se o arquivo é uma imagem válida."""
        extensoes_validas = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        extensao = os.path.splitext(caminho_imagem.lower())[1]
        return extensao in extensoes_validas

    def _converter_para_base64(self, caminho_imagem):
        """Converte uma imagem local para base64."""
        try:
            mime_type, _ = mimetypes.guess_type(caminho_imagem)
            if not mime_type or not mime_type.startswith('image/'):
                # Default para JPEG se não conseguir detectar
                mime_type = 'image/jpeg'

            with open(caminho_imagem, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

            return f"data:{mime_type};base64,{encoded_string}"

        except Exception as e:
            print(f"Erro ao converter imagem para base64: {e}")
            return None

    def _fazer_requisicao(self, payload):
        """Faz a requisição HTTP para a API."""
        try:
            url = f"{self.base_url}/send-image"
            params = {"instanceId": self.instance_id}

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                params=params,
                timeout=30
            )

            try:
                result = response.json()

                if response.status_code == 200:
                    return {
                        "success": True,
                        "data": result,
                        "status_code": response.status_code,
                        "message": "Imagem enviada com sucesso"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Erro HTTP {response.status_code}",
                        "details": result,
                        "status_code": response.status_code
                    }

            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": f"Erro HTTP {response.status_code} - Resposta inválida",
                    "response_text": response.text[:200],
                    "status_code": response.status_code
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout - Requisição demorou muito"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Erro de conexão - Verifique a internet"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Erro na requisição: {str(e)}"
            }


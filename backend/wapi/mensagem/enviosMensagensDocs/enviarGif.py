import requests
import json
import base64
import os
import mimetypes
from urllib.parse import urlparse


class EnviaGif:
    """Classe para enviar GIFs via WhatsApp usando a API W-API."""

    def __init__(self, instance_id, api_token, base_url="https://api.w-api.app/v1/message"):
        """
        Inicializa a classe EnviaGif.

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

    def enviar(self, phone_number, gif_source, caption="", delay_message=1):
        """
        Envia GIF via WhatsApp.
        Detecta automaticamente se é URL ou caminho local (ex: C:\\Users\\pasta\\arquivo.mp4).

        Args:
            phone_number (str): Número de telefone do destinatário.
            gif_source (str): URL do GIF/MP4 ou caminho local do arquivo.
            caption (str): Legenda do GIF (opcional).
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

        # Debug: mostra o que foi detectado
        is_url = self._is_url(gif_source)
        print(f"📍 Fonte detectada: {'URL' if is_url else 'Arquivo Local'}")
        print(f"📂 Caminho/URL: {gif_source}")

        # Detecta se é URL ou arquivo local
        if is_url:
            return self._enviar_url(phone_number, gif_source, caption, delay_message)
        else:
            return self._enviar_arquivo_local(phone_number, gif_source, caption, delay_message)

    def _is_url(self, string):
        """Verifica se a string é uma URL válida."""
        try:
            # Verifica se começa com http/https
            if string.startswith(('http://', 'https://')):
                result = urlparse(string)
                return all([result.scheme, result.netloc])

            # Se contém :\ ou / no início, provavelmente é caminho local
            if ':\\' in string or string.startswith('/') or string.startswith('./') or string.startswith('../'):
                return False

            # Verifica se é URL sem protocolo
            if '.' in string and not os.path.exists(string):
                return True

            return False
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

    def _enviar_url(self, phone_number, gif_url, caption, delay_message):
        """Envia GIF via URL."""
        try:
            payload = {
                "phone": phone_number,
                "gif": gif_url,
                "delayMessage": delay_message
            }

            if caption:
                payload["caption"] = caption

            return self._fazer_requisicao(payload)

        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao enviar GIF por URL: {str(e)}"
            }

    def _enviar_arquivo_local(self, phone_number, caminho_gif, caption, delay_message):
        """Processa e envia GIF/MP4 local."""
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(caminho_gif):
                return {
                    "success": False,
                    "error": f"Arquivo não encontrado: {caminho_gif}",
                    "details": "Verifique se o caminho está correto"
                }

            # Verifica se é um arquivo válido para GIF
            if not self._is_gif_valido(caminho_gif):
                return {
                    "success": False,
                    "error": "Arquivo não é um GIF/MP4 válido",
                    "details": "Formatos suportados: .gif, .mp4, .mov, .avi"
                }

            # Converte para base64
            gif_base64 = self._converter_para_base64(caminho_gif)
            if not gif_base64:
                return {
                    "success": False,
                    "error": "Erro ao converter arquivo para base64"
                }

            # Prepara payload
            payload = {
                "phone": phone_number,
                "gif": gif_base64,
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

    def _is_gif_valido(self, caminho_arquivo):
        """Verifica se o arquivo é um GIF/vídeo válido."""
        extensoes_validas = {'.gif', '.mp4', '.mov', '.avi', '.webm'}
        extensao = os.path.splitext(caminho_arquivo.lower())[1]
        return extensao in extensoes_validas

    def _converter_para_base64(self, caminho_arquivo):
        """Converte um arquivo local para base64."""
        try:
            mime_type, _ = mimetypes.guess_type(caminho_arquivo)

            # Se não conseguir detectar, assume baseado na extensão
            if not mime_type:
                extensao = os.path.splitext(caminho_arquivo.lower())[1]
                if extensao == '.gif':
                    mime_type = 'image/gif'
                elif extensao == '.mp4':
                    mime_type = 'video/mp4'
                elif extensao == '.mov':
                    mime_type = 'video/quicktime'
                elif extensao == '.avi':
                    mime_type = 'video/x-msvideo'
                else:
                    mime_type = 'video/mp4'  # Default

            with open(caminho_arquivo, "rb") as arquivo:
                encoded_string = base64.b64encode(arquivo.read()).decode('utf-8')

            return f"data:{mime_type};base64,{encoded_string}"

        except Exception as e:
            print(f"Erro ao converter arquivo para base64: {e}")
            return None

    def _fazer_requisicao(self, payload):
        """Faz a requisição HTTP para a API."""
        try:
            url = f"{self.base_url}/send-gif"
            params = {"instanceId": self.instance_id}

            response = requests.post(
                url,
                headers=self.headers,
                params=params,
                data=json.dumps(payload),  # Usando data em vez de json como no exemplo
                timeout=30
            )

            print(f"Status Code: {response.status_code}")
            print(f"URL: {response.url}")

            try:
                result = response.json()

                if response.status_code == 200:
                    return {
                        "success": True,
                        "data": result,
                        "status_code": response.status_code,
                        "message": "GIF enviado com sucesso"
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



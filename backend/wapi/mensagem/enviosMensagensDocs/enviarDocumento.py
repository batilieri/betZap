import requests
import json
import os
import base64
from pathlib import Path


class EnviaDocumento:
    def __init__(self, base_url, instance_name, api_key):
        """
        Inicializa a classe para envio de documentos

        Args:
            base_url (str): URL base da API
            instance_name (str): Nome da instância do WhatsApp
            api_key (str): Chave da API para autenticação
        """
        self.base_url = base_url.rstrip('/')
        self.instance_name = instance_name
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

    def enviar_arquivo_local(self, telefone, caminho_arquivo, legenda="", delay=2):
        """
        Envia um arquivo local convertendo para Base64

        Args:
            telefone (str): Número do destinatário (ex: "5569993291093")
            caminho_arquivo (str): Caminho completo do arquivo
            legenda (str): Legenda opcional para o arquivo
            delay (int): Delay em segundos (padrão: 15)

        Returns:
            dict: Resultado do envio
        """
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(caminho_arquivo):
                return {
                    'success': False,
                    'error': f'Arquivo não encontrado: {caminho_arquivo}'
                }

            # Obter informações do arquivo
            arquivo_path = Path(caminho_arquivo)
            nome_arquivo = arquivo_path.name
            extensao = arquivo_path.suffix.lower().replace('.', '')  # Remove o ponto

            # Ler arquivo e converter para base64
            with open(caminho_arquivo, 'rb') as arquivo:
                conteudo_arquivo = arquivo.read()
                conteudo_base64 = base64.b64encode(conteudo_arquivo).decode('utf-8')

            # Determinar tipo MIME
            mime_types = {
                'pdf': 'application/pdf',
                'doc': 'application/msword',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'xls': 'application/vnd.ms-excel',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'txt': 'text/plain',
                'zip': 'application/zip',
                'rar': 'application/x-rar-compressed',
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
                'mp4': 'video/mp4',
                'mp3': 'audio/mpeg',
                'wav': 'audio/wav'
            }

            mime_type = mime_types.get(extensao, 'application/octet-stream')

            # Preparar URL da API (URL correta conforme documentação)
            url = f"{self.base_url}/message/send-document?instanceId={self.instance_name}"

            # Preparar payload conforme a documentação da API
            payload = {
                "phone": telefone,
                "document": f"data:{mime_type};base64,{conteudo_base64}",
                "extension": extensao,
                "fileName": nome_arquivo,
                "caption": legenda,
                "delayMessage": delay
            }

            # Log para debug
            print(f"🔍 DEBUG INFO:")
            print(f"URL: {url}")
            print(f"Headers: {self.headers}")
            print(f"Payload (sem base64): {dict(payload, document='[BASE64_DATA]')}")
            print(f"Tamanho do Base64: {len(conteudo_base64)} caracteres")
            print("-" * 50)

            # Fazer requisição
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            return {
                'success': True,
                'data': response.json(),
                'status_code': response.status_code,
                'arquivo_info': {
                    'nome': nome_arquivo,
                    'extensao': extensao,
                    'tamanho_mb': round(len(conteudo_arquivo) / (1024 * 1024), 2)
                }
            }

        except requests.exceptions.RequestException as e:
            print(f"❌ ERRO DE REQUISIÇÃO:")
            print(f"Status Code: {getattr(e.response, 'status_code', 'N/A')}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Resposta da API: {e.response.text}")
            print(f"Erro: {str(e)}")
            print("-" * 50)

            return {
                'success': False,
                'error': f'Erro na requisição: {str(e)}',
                'status_code': getattr(e.response, 'status_code', None),
                'response_text': getattr(e.response, 'text', None) if hasattr(e, 'response') else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro geral: {str(e)}'
            }

    def obter_info_arquivo(self, caminho_arquivo):
        """
        Obtém informações detalhadas sobre um arquivo

        Args:
            caminho_arquivo (str): Caminho do arquivo

        Returns:
            dict: Informações do arquivo
        """
        try:
            if not os.path.exists(caminho_arquivo):
                return {
                    'existe': False,
                    'erro': 'Arquivo não encontrado'
                }

            arquivo_path = Path(caminho_arquivo)
            stat = arquivo_path.stat()

            return {
                'existe': True,
                'nome': arquivo_path.name,
                'extensao': arquivo_path.suffix.replace('.', ''),
                'tamanho_bytes': stat.st_size,
                'tamanho_mb': round(stat.st_size / (1024 * 1024), 2),
                'caminho_completo': str(arquivo_path.absolute())
            }
        except Exception as e:
            return {
                'existe': False,
                'erro': str(e)
            }



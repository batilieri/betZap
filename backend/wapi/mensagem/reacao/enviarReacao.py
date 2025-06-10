import requests
import json


class EnviarReacao:
    def __init__(self, instance_id, token):
        """
        Inicializa o enviador de reações

        Args:
            instance_id (str): ID da instância do WhatsApp
            token (str): Token de autorização da API
        """
        self.instance_id = instance_id
        self.token = token
        self.base_url = "https://api.w-api.app/v1/message/send-reaction"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def enviar_reacao(self, phone, message_id, reaction, delay=0):
        """
        Envia uma reação para uma mensagem

        Args:
            phone (str): Número do telefone ou grupo (formato: 5569999267344)
            message_id (str): ID da mensagem para reagir
            reaction (str): Emoji da reação (ex: "😉", "❤️", "👍")
            delay (int): Atraso opcional em segundos (padrão: 0)

        Returns:
            dict: Resposta da API com status e dados
        """
        params = {
            "instanceId": self.instance_id
        }

        payload = {
            "phone": phone,
            "reaction": reaction,
            "messageId": message_id
        }

        # Adiciona delay apenas se for maior que 0
        if delay > 0:
            payload["delayMessage"] = delay

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                params=params,
                data=json.dumps(payload)
            )

            resultado = {
                "sucesso": response.status_code == 200,
                "status_code": response.status_code,
                "dados": response.json() if response.status_code == 200 else None,
                "erro": response.text if response.status_code != 200 else None
            }

            return resultado

        except requests.exceptions.RequestException as e:
            return {
                "sucesso": False,
                "status_code": None,
                "dados": None,
                "erro": f"Erro na requisição: {str(e)}"
            }
        except json.JSONDecodeError:
            return {
                "sucesso": False,
                "status_code": response.status_code,
                "dados": None,
                "erro": "Erro ao decodificar resposta JSON"
            }

    def enviar_reacao_simples(self, phone, message_id, reaction, delay=0):
        """
        Versão simplificada que retorna apenas sucesso/erro

        Returns:
            bool: True se enviou com sucesso, False caso contrário
        """
        resultado = self.enviar_reacao(phone, message_id, reaction, delay)
        return resultado["sucesso"]

    def reacoes_comuns(self):
        """
        Retorna dicionário com reações comuns

        Returns:
            dict: Emojis organizados por categoria
        """
        return {
            "positivas": ["👍", "❤️", "😍", "🔥", "👏", "🎉"],
            "negativas": ["👎", "😢", "😡", "💔"],
            "expressoes": ["😂", "😮", "😉", "🤔", "😴", "🤯"],
            "simbolos": ["💯", "⭐", "✅", "❌", "⚡", "💎"]
        }



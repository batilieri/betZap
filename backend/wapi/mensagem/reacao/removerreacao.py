import requests
import json
from typing import Optional, Dict, Any


class RemoverReacao:
    """
    Classe para remover reações de mensagens usando a API W-API.
    """

    def __init__(self, instance_id: str, token: str):
        """
        Inicializa a classe com as credenciais da API.

        Args:
            instance_id (str): ID da instância do WhatsApp
            token (str): Token de autorização da API
        """
        self.instance_id = instance_id
        self.token = token
        self.base_url = "https://api.w-api.app/v1"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def remover_reacao(self, phone: str, message_id: str, delay_message: Optional[int] = None) -> Dict[str, Any]:
        """
        Remove uma reação de uma mensagem específica.

        Args:
            phone (str): Número do telefone (formato: 559199999999)
            message_id (str): ID da mensagem da qual remover a reação
            delay_message (int, optional): Delay em segundos antes de enviar

        Returns:
            Dict[str, Any]: Resposta da API ou erro
        """
        url = f"{self.base_url}/message/remove-reaction"

        # Parâmetros de query
        params = {"instanceId": self.instance_id}

        # Payload da requisição
        payload = {
            "phone": phone,
            "messageId": message_id
        }

        # Adicionar delay se fornecido
        if delay_message is not None:
            payload["delayMessage"] = delay_message

        try:
            # Fazer a requisição
            response = requests.post(
                url,
                headers=self.headers,
                params=params,
                data=json.dumps(payload)
            )

            # Verificar status da resposta
            if response.status_code == 200:
                return {
                    "sucesso": True,
                    "status_code": response.status_code,
                    "dados": response.json(),
                    "mensagem": "Reação removida com sucesso!"
                }
            else:
                return {
                    "sucesso": False,
                    "status_code": response.status_code,
                    "erro": response.text,
                    "mensagem": f"Erro ao remover reação: {response.status_code}"
                }

        except requests.exceptions.RequestException as e:
            return {
                "sucesso": False,
                "status_code": None,
                "erro": str(e),
                "mensagem": "Erro de conexão com a API"
            }

    def remover_multiplas_reacoes(self, reacoes: list) -> list:
        """
        Remove múltiplas reações de uma vez.

        Args:
            reacoes (list): Lista de dicionários com 'phone', 'message_id' e opcionalmente 'delay_message'

        Returns:
            list: Lista com os resultados de cada remoção
        """
        resultados = []

        for reacao in reacoes:
            phone = reacao.get('phone')
            message_id = reacao.get('message_id')
            delay_message = reacao.get('delay_message')

            if not phone or not message_id:
                resultados.append({
                    "sucesso": False,
                    "erro": "Phone e message_id são obrigatórios",
                    "dados_entrada": reacao
                })
                continue

            resultado = self.remover_reacao(phone, message_id, delay_message)
            resultado["dados_entrada"] = reacao
            resultados.append(resultado)

        return resultados



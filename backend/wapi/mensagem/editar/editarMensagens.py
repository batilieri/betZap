import requests
import json


class EditarMensagem:
    def __init__(self, instance_id, token):
        """
        Inicializa o editor de mensagens

        Args:
            instance_id (str): ID da instância do WhatsApp
            token (str): Token de autorização da API
        """
        self.instance_id = instance_id
        self.token = token
        self.base_url = "https://api.w-api.app/v1/message"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }

    def editar_mensagem(self, phone, message_id, new_text):
        """
        Edita uma mensagem já enviada

        Args:
            phone (str): Número do telefone (formato: 5569999267344)
            message_id (str): ID da mensagem a ser editada
            new_text (str): Novo texto da mensagem

        Returns:
            dict: Resposta da API
        """
        url = f'{self.base_url}/edit-message?instanceId={self.instance_id}'

        data = {
            "phone": phone,
            "text": new_text,
            "messageId": message_id
        }

        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()  # Levanta exceção para códigos de erro HTTP
            return response.json()

        except requests.exceptions.RequestException as e:
            return {"erro": f"Erro na requisição: {str(e)}"}
        except json.JSONDecodeError:
            return {"erro": "Erro ao decodificar resposta JSON"}

    def editar_mensagem_simples(self, phone, message_id, new_text):
        """
        Versão simplificada que retorna apenas sucesso/erro

        Returns:
            bool: True se editou com sucesso, False caso contrário
        """
        resultado = self.editar_mensagem(phone, message_id, new_text)
        return "erro" not in resultado




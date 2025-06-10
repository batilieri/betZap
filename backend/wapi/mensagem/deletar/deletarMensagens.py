import requests
import json


class DeletaMensagem:
    """Classe ultra simplificada para deletar mensagens no WhatsApp."""

    def __init__(self, instance_id, api_token, base_url="https://api.w-api.app/v1/message"):
        self.instance_id = instance_id
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_token}'
        }

    def deletar(self, phone_number, message_ids):
        """
        Método único para deletar mensagens.
        Aceita automaticamente uma mensagem ou várias.

        Args:
            phone_number (str): Número de telefone ou ID do grupo.
            message_ids (str ou list):
                - String: deleta uma mensagem
                - Lista: deleta várias mensagens

        Returns:
            dict: Resultado da operação.
        """
        try:
            # Validação básica
            if not phone_number or not phone_number.strip():
                return {"success": False, "error": "Número é obrigatório"}

            if not message_ids:
                return {"success": False, "error": "Message ID(s) obrigatório(s)"}

            phone_clean = phone_number.strip()

            # Detecta automaticamente se é uma ou várias mensagens
            if isinstance(message_ids, str):
                # Uma mensagem
                return self._deletar_uma(phone_clean, message_ids.strip())

            elif isinstance(message_ids, list):
                # Várias mensagens
                return self._deletar_varias(phone_clean, message_ids)

            else:
                return {"success": False, "error": "message_ids deve ser string ou lista"}

        except Exception as e:
            return {"success": False, "error": f"Erro: {str(e)}"}

    def _deletar_uma(self, phone, message_id):
        """Deleta uma mensagem."""
        try:
            url = f"{self.base_url}/delete-message"
            params = {
                'phone': phone,
                'messageId': message_id,
                'instanceId': self.instance_id
            }

            response = requests.delete(
                url,
                headers=self.headers,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "message": "Mensagem deletada",
                    "deletadas": 1
                }
            else:
                try:
                    error_data = response.json()
                except:
                    error_data = response.text[:200]

                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "details": error_data
                }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Sem conexão"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _deletar_varias(self, phone, message_ids_list):
        """Deleta várias mensagens."""
        if not message_ids_list:
            return {"success": False, "error": "Lista vazia"}

        sucessos = 0
        erros = 0
        detalhes = []

        for msg_id in message_ids_list:
            try:
                if not msg_id or not str(msg_id).strip():
                    erros += 1
                    detalhes.append("❌ ID vazio")
                    continue

                resultado = self._deletar_uma(phone, str(msg_id).strip())

                if resultado["success"]:
                    sucessos += 1
                    detalhes.append(f"✅ {msg_id}")
                else:
                    erros += 1
                    detalhes.append(f"❌ {msg_id}: {resultado['error']}")

            except Exception as e:
                erros += 1
                detalhes.append(f"❌ {msg_id}: erro")

        return {
            "success": sucessos > 0,
            "deletadas": sucessos,
            "erros": erros,
            "total": len(message_ids_list),
            "detalhes": detalhes,
            "message": f"Deletadas: {sucessos}/{len(message_ids_list)}"
        }

#
# # Exemplo de uso ultra simples
# if __name__ == "__main__":
#     deleter = DeletaMensagem("3B6XIW-ZTS923-GEAY6V", "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF")
#
#     # # 1. Deletar UMA mensagem (string)
#     # result1 = deleter.deletar("556992884107", "E8894400327F529368A1A0FA16A72B35")
#     # print(result1)
#
#     # 2. Deletar VÁRIAS mensagens (lista)
#     result2 = deleter.deletar("556992884107",
#                               ["2B1589F6BEFBE1309F28CCDE1FBDE530",
#                                "2B1589F6BEFBE1309F28CCDE1FBDE530",
#                                "4016959CEB34368628C2E05B62070B85"])
#     #
#     # # 3. Lista com uma mensagem (também funciona)
#     # result3 = deleter.deletar("5569999267344", ["MSG_UNICA"])
#

import requests
from typing import Optional, Dict, Any, List


class LerMensagem:
    """
    Classe para marcar mensagens como lidas usando a API W-API.
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
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

    def marcar_como_lida(self, phone: str, message_id: str) -> Dict[str, Any]:
        """
        Marca uma mensagem específica como lida.

        Args:
            phone (str): Número do telefone (formato: 559199999999)
            message_id (str): ID da mensagem para marcar como lida

        Returns:
            Dict[str, Any]: Resposta da API ou erro
        """
        url = f"{self.base_url}/message/read-message?instanceId={self.instance_id}"

        # Dados da requisição
        data = {
            "phone": phone,
            "messageId": message_id
        }

        try:
            response = requests.post(url, json=data, headers=self.headers)

            if response.status_code == 200:
                return {
                    "sucesso": True,
                    "status_code": response.status_code,
                    "dados": response.json(),
                    "mensagem": "Mensagem marcada como lida com sucesso!",
                    "phone": phone,
                    "message_id": message_id
                }
            else:
                return {
                    "sucesso": False,
                    "status_code": response.status_code,
                    "erro": response.text,
                    "mensagem": f"Erro ao marcar mensagem como lida: {response.status_code}",
                    "phone": phone,
                    "message_id": message_id
                }

        except requests.exceptions.RequestException as e:
            return {
                "sucesso": False,
                "status_code": None,
                "erro": str(e),
                "mensagem": "Erro de conexão com a API",
                "phone": phone,
                "message_id": message_id
            }

    def marcar_multiplas_como_lidas(self, mensagens: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Marca múltiplas mensagens como lidas de uma vez.

        Args:
            mensagens (list): Lista de dicionários com 'phone' e 'message_id'

        Returns:
            list: Lista com os resultados de cada marcação
        """
        resultados = []

        for mensagem in mensagens:
            phone = mensagem.get('phone')
            message_id = mensagem.get('message_id')

            if not phone or not message_id:
                resultados.append({
                    "sucesso": False,
                    "erro": "Phone e message_id são obrigatórios",
                    "dados_entrada": mensagem
                })
                continue

            resultado = self.marcar_como_lida(phone, message_id)
            resultado["dados_entrada"] = mensagem
            resultados.append(resultado)

        return resultados

    def marcar_conversa_como_lida(self, phone: str, message_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Marca todas as mensagens de uma conversa como lidas.

        Args:
            phone (str): Número do telefone
            message_ids (list): Lista de IDs das mensagens

        Returns:
            list: Lista com os resultados de cada marcação
        """
        resultados = []

        for message_id in message_ids:
            resultado = self.marcar_como_lida(phone, message_id)
            resultados.append(resultado)

        return resultados

    def obter_estatisticas(self, resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula estatísticas dos resultados de marcação.

        Args:
            resultados (list): Lista de resultados das marcações

        Returns:
            dict: Estatísticas dos resultados
        """
        total = len(resultados)
        sucessos = sum(1 for r in resultados if r.get("sucesso"))
        erros = total - sucessos

        return {
            "total_mensagens": total,
            "sucessos": sucessos,
            "erros": erros,
            "taxa_sucesso": round((sucessos / total * 100), 2) if total > 0 else 0,
            "detalhes_erros": [
                {
                    "phone": r.get("phone"),
                    "message_id": r.get("message_id"),
                    "erro": r.get("erro")
                }
                for r in resultados if not r.get("sucesso")
            ]
        }


# Exemplo de uso
if __name__ == "__main__":
    # Configurar suas credenciais
    INSTANCE_ID = "3B6XIW-ZTS923-GEAY6V"
    TOKEN = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"

    # Criar instância da classe
    leitor = LerMensagem(INSTANCE_ID, TOKEN)

    # Exemplo 1: Marcar uma mensagem única como lida
    resultado = leitor.marcar_como_lida(
        phone="5569993291093",
        message_id="ID_DA_MENSAGEM"
    )

    print("Resultado único:")
    if resultado["sucesso"]:
        print("✅", resultado["mensagem"])
        print("Dados:", resultado["dados"])
    else:
        print("❌", resultado["mensagem"])
        print("Erro:", resultado["erro"])

    print("\n" + "=" * 50 + "\n")

    # Exemplo 2: Marcar múltiplas mensagens como lidas
    lista_mensagens = [
        {
            "phone": "559199999999",
            "message_id": "ID_MENSAGEM_1"
        },
        {
            "phone": "559188888888",
            "message_id": "ID_MENSAGEM_2"
        },
        {
            "phone": "559177777777",
            "message_id": "ID_MENSAGEM_3"
        }
    ]

    resultados_multiplos = leitor.marcar_multiplas_como_lidas(lista_mensagens)

    print("Resultados múltiplos:")
    for i, resultado in enumerate(resultados_multiplos, 1):
        print(f"\nMensagem {i}:")
        if resultado["sucesso"]:
            print("✅", resultado["mensagem"])
        else:
            print("❌", resultado["mensagem"])
            print("Erro:", resultado["erro"])

    print("\n" + "=" * 50 + "\n")

    # Exemplo 3: Marcar toda uma conversa como lida
    phone_conversa = "559199999999"
    ids_conversa = ["MSG_1", "MSG_2", "MSG_3", "MSG_4"]

    resultados_conversa = leitor.marcar_conversa_como_lida(phone_conversa, ids_conversa)

    print("Resultados da conversa:")
    estatisticas = leitor.obter_estatisticas(resultados_conversa)
    print(f"📊 Total: {estatisticas['total_mensagens']}")
    print(f"✅ Sucessos: {estatisticas['sucessos']}")
    print(f"❌ Erros: {estatisticas['erros']}")
    print(f"📈 Taxa de sucesso: {estatisticas['taxa_sucesso']}%")

    if estatisticas['detalhes_erros']:
        print("\nDetalhes dos erros:")
        for erro in estatisticas['detalhes_erros']:
            print(f"- {erro['phone']} | {erro['message_id']}: {erro['erro']}")
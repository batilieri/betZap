import requests
import json


class WAPICallReject:
    def __init__(self, base_url="https://api.w-api.app/v1", bearer_token="Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"):
        """
        Inicializa a classe com a URL base da API e o token de autorização

        Args:
            base_url (str): URL base da API W-API
            bearer_token (str): Token de autorização Bearer
        """
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}"
        }

    def enable_call_reject(self, instance_id, enable=True):
        """
        Habilita ou desabilita a rejeição automática de chamadas

        Args:
            instance_id (str): ID da instância
            enable (bool): True para habilitar, False para desabilitar

        Returns:
            dict: Resposta da API
        """
        url = f"{self.base_url}/instance/update-call-reject-auto"
        params = {"instanceId": instance_id}
        data = {"value": enable}

        try:
            response = requests.put(
                url,
                headers=self.headers,
                params=params,
                json=data
            )
            response.raise_for_status()
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.content else {}
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }

    def set_call_reject_message(self, instance_id, message):
        """
        Define a mensagem que será enviada após rejeitar uma chamada

        Args:
            instance_id (str): ID da instância
            message (str): Mensagem personalizada

        Returns:
            dict: Resposta da API
        """
        url = f"{self.base_url}/instance/update-call-reject-message"
        params = {"instanceId": instance_id}
        data = {"value": message}

        try:
            response = requests.put(
                url,
                headers=self.headers,
                params=params,
                json=data
            )
            response.raise_for_status()
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.content else {}
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None)
            }


# Exemplo de uso
def main():
    # Configurações
    BEARER_TOKEN = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"  # Substitua pelo seu token
    INSTANCE_ID = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"  # Substitua pelo ID da sua instância

    # Inicializar a classe
    api = WAPICallReject(bearer_token=BEARER_TOKEN)

    print("🔧 Configurando rejeição automática de chamadas...")
    print("-" * 50)

    # 1. Habilitar rejeição automática de chamadas
    print("1️⃣ Habilitando rejeição automática...")
    result = api.enable_call_reject(INSTANCE_ID, enable=True)

    if result["success"]:
        print("✅ Rejeição automática habilitada com sucesso!")
        print(f"Status Code: {result['status_code']}")
    else:
        print("❌ Erro ao habilitar rejeição automática:")
        print(f"Erro: {result['error']}")
        return

    print()

    # 2. Definir mensagem personalizada
    print("2️⃣ Configurando mensagem personalizada...")
    custom_message = """
🚫 Chamada automaticamente rejeitada

Olá! No momento não posso atender chamadas de voz ou vídeo.
Por favor, envie uma mensagem de texto que responderei assim que possível.

Obrigado pela compreensão! 😊
    """.strip()

    result = api.set_call_reject_message(INSTANCE_ID, custom_message)

    if result["success"]:
        print("✅ Mensagem personalizada configurada com sucesso!")
        print(f"Status Code: {result['status_code']}")
        print(f"Mensagem definida: {custom_message}")
    else:
        print("❌ Erro ao configurar mensagem:")
        print(f"Erro: {result['error']}")

    print()
    print("🎉 Configuração concluída!")


# Exemplo adicional: Desabilitar rejeição automática
def disable_call_reject_example():
    BEARER_TOKEN = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"
    INSTANCE_ID = "3B6XIW-ZTS923-GEAY6V"

    api = WAPICallReject(bearer_token=BEARER_TOKEN)

    print("🔄 Desabilitando rejeição automática de chamadas...")
    result = api.enable_call_reject(INSTANCE_ID, enable=False)

    if result["success"]:
        print("✅ Rejeição automática desabilitada!")
    else:
        print(f"❌ Erro: {result['error']}")


# Executar exemplo
if __name__ == "__main__":
    print("🤖 Configuração de Rejeição de Chamadas")
    print("=" * 50)

    # Verificar se requests está instalado
    try:
        import requests
    except ImportError:
        print("❌ Biblioteca 'requests' não encontrada!")
        print("💡 Execute: pip install requests")
        exit(1)

    # Executar configuração principal
    main()

    print("\n" + "=" * 50)
    print("📝 Lembre-se de:")
    print("• Substituir SEU_TOKEN_AQUI pelo seu token Bearer")
    print("• Substituir SUA_INSTANCIA_AQUI pelo ID da sua instância")
    print("• Personalizar a mensagem conforme necessário")
    print("• Testar com uma chamada para verificar o funcionamento")
import requests
import json

class WAPIWebhookManager:
    """
    Classe para auto-configuração de Webhooks na W-API (WhizAPI) via requests.
    Permite configurar webhooks de envio e recebimento para integração com webhook.site
    """

    def __init__(self, instance_id, api_token, webhook_site_url):
        """
        Inicializa a configuração.
        :param instance_id: str - ID da instância na W-API.
        :param api_token: str - Token de autorização da W-API.
        :param webhook_site_url: str - URL completa do webhook.site.
        """
        self.instance_id = instance_id
        self.api_token = api_token
        self.webhook_site_url = webhook_site_url

        self.base_url = "https://api.w-api.app/v1/webhook"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }

    def configurar_webhook_envio(self):
        """
        Configura o webhook de envio na W-API.
        """
        url = f"{self.base_url}/update-webhook-delivery?instanceId={self.instance_id}"
        payload = {"value": self.webhook_site_url}

        print(f"🔧 Configurando webhook de ENVIO...")
        response = requests.put(url, headers=self.headers, json=payload, timeout=10)
        return self._tratar_resposta(response, "envio")

    def configurar_webhook_recebimento(self):
        """
        Configura o webhook de recebimento na W-API.
        """
        url = f"{self.base_url}/update-webhook-received?instanceId={self.instance_id}"
        payload = {"value": self.webhook_site_url}

        print(f"🔧 Configurando webhook de RECEBIMENTO...")
        response = requests.put(url, headers=self.headers, json=payload, timeout=10)
        return self._tratar_resposta(response, "recebimento")

    def _tratar_resposta(self, response, tipo):
        """
        Trata a resposta da API.
        """
        if response.status_code == 200:
            data = response.json()
            if not data.get("error"):
                print(f"✅ Webhook de {tipo} configurado com sucesso: {data.get('message')}")
                return True
            else:
                print(f"❌ Erro na configuração de {tipo}: {data}")
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
        return False

    def verificar_webhook_site(self):
        """
        Testa a URL do webhook.site diretamente.
        """
        print(f"🔍 Verificando acesso ao webhook.site: {self.webhook_site_url}")
        try:
            response = requests.get(self.webhook_site_url, timeout=10)
            print(f"📊 Status: {response.status_code}")
            print(f"📏 Tamanho: {len(response.text)} chars")
            print(f"📄 Conteúdo inicial: {response.text[:500]}...")
        except Exception as e:
            print(f"❌ Erro ao acessar webhook.site: {e}")

    def configurar_tudo(self):
        """
        Executa a configuração completa de ambos os webhooks.
        """
        print("🚀 Iniciando configuração completa de Webhooks W-API...")
        self.configurar_webhook_envio()
        self.configurar_webhook_recebimento()
        self.verificar_webhook_site()
        print("✅ Configuração finalizada.")


if __name__ == "__main__":
    INSTANCE_ID = "3B6XIW-ZTS923-GEAY6V"
    API_TOKEN = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"
    WEBHOOK_SITE_URL = "https://webhook.site/0e6e92fd-c357-44e4-b1e5-067d6ae4cd0d"

    gestor_webhook = WAPIWebhookManager(INSTANCE_ID, API_TOKEN, WEBHOOK_SITE_URL)

    # Configuração completa
    gestor_webhook.configurar_tudo()

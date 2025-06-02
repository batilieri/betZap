import requests

# ✅ CONFIGURAÇÕES
INSTANCE_ID = '3B6XIW-ZTS923-GEAY6V'
TOKEN = 'Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF'


def configurar_webhook_com_url(ngrok_url):
    """Configura o webhook com a URL do ngrok"""

    # Garante que a URL termine com /webhook
    if not ngrok_url.endswith('/webhook'):
        webhook_url = f"{ngrok_url.rstrip('/')}/webhook"
    else:
        webhook_url = ngrok_url

    print(f"🔧 Configurando webhook para: {webhook_url}")

    url = f'https://api.w-api.app/v1/webhook/update-webhook-delivery?instanceId={INSTANCE_ID}'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {TOKEN}'
    }

    payload = {
        "value": webhook_url
    }

    try:
        response = requests.put(url, headers=headers, json=payload)

        if response.status_code == 200:
            print('✅ Webhook configurado com sucesso!')
            print(f'🌐 URL ativa: {webhook_url}')
            print('📱 Agora as mensagens aparecerão no seu terminal!')
            return True
        else:
            print(f'⚠️ Erro na configuração: código {response.status_code}')
            print('Resposta:', response.text)
            return False

    except Exception as e:
        print(f'❌ Erro inesperado: {e}')
        return False


if __name__ == '__main__':
    print("🔧 CONFIGURADOR DE WEBHOOK")
    print("=" * 30)

    print("📋 Passos:")
    print("1. Execute: ngrok http 5000")
    print("2. Copie a URL HTTPS (ex: https://abc123.ngrok.io)")
    print("3. Cole aqui abaixo")
    print()

    ngrok_url = input("🌐 Cole sua URL do ngrok: ").strip()

    if ngrok_url:
        configurar_webhook_com_url(ngrok_url)
    else:
        print("❌ URL não fornecida!")
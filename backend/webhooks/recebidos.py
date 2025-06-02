import requests
import time
from datetime import datetime

# ✅ SUAS CONFIGURAÇÕES
INSTANCE_ID = '3B6XIW-ZTS923-GEAY6V'
TOKEN = 'Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF'


def buscar_mensagens_webhook():
    """Busca mensagens do webhook.site"""

    # Cole aqui sua URL do webhook.site (a parte única)
    WEBHOOK_ID = input("📥 Cole o ID do seu webhook.site (ex: b843e182-e69e-4a23-86ca-3efc2efc506d): ").strip()

    if not WEBHOOK_ID:
        print("❌ ID do webhook não fornecido!")
        return

    webhook_api_url = f"https://webhook.site/token/{WEBHOOK_ID}/requests"

    print(f"🔍 Buscando mensagens de: {webhook_api_url}")
    print("📱 Mensagens aparecerão abaixo...\n")

    mensagens_vistas = set()

    while True:
        try:
            # Busca as requisições recebidas no webhook.site
            response = requests.get(webhook_api_url)

            if response.status_code == 200:
                requests_data = response.json()

                # Processa cada requisição
                for req in requests_data.get('data', []):
                    req_id = req.get('uuid')

                    if req_id not in mensagens_vistas:
                        content = req.get('content')

                        if content and isinstance(content, str):
                            try:
                                import json
                                message_data = json.loads(content)

                                # Verifica se é uma mensagem do WhatsApp
                                if message_data.get('event') == 'webhookReceived':
                                    processar_mensagem(message_data)
                                    mensagens_vistas.add(req_id)

                            except json.JSONDecodeError:
                                pass

            time.sleep(3)  # Verifica a cada 3 segundos

        except KeyboardInterrupt:
            print("\n👋 Busca interrompida!")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            time.sleep(5)


def processar_mensagem(data):
    """Processa e exibe a mensagem de forma organizada"""

    print('\n' + '=' * 60)
    print('📱 NOVA MENSAGEM RECEBIDA!')
    print('=' * 60)

    # Informações básicas
    print(f"🆔 Message ID: {data.get('messageId', 'N/A')}")
    print(f"📞 Instance: {data.get('instanceId', 'N/A')}")
    print(f"📱 Conectado: {data.get('connectedPhone', 'N/A')}")
    print(f"👥 É grupo: {'Sim' if data.get('isGroup') else 'Não'}")
    print(f"📤 De mim: {'Sim' if data.get('fromMe') else 'Não'}")

    # Informações do remetente
    sender = data.get('sender', {})
    print(f"👤 Remetente: {sender.get('pushName', 'N/A')}")
    print(f"📞 Número: {sender.get('id', 'N/A')}")

    if sender.get('verifiedBizName'):
        print(f"🏢 Empresa: {sender.get('verifiedBizName')}")

    # Conteúdo da mensagem
    msg_content = data.get('msgContent', {})
    conversation = msg_content.get('conversation', '')

    print(f"💬 MENSAGEM: {conversation}")

    # Timestamp
    moment = data.get('moment')
    if moment:
        dt = datetime.fromtimestamp(moment)
        print(f"🕐 Quando: {dt.strftime('%d/%m/%Y %H:%M:%S')}")

    # Chat info
    chat = data.get('chat', {})
    print(f"💭 Chat ID: {chat.get('id', 'N/A')}")

    print('=' * 60 + '\n')


def buscar_via_api():
    """Tenta buscar mensagens diretamente da API W-API"""

    print("🔍 Tentando buscar mensagens diretamente da API...")

    # Possíveis endpoints
    endpoints = [
        f'https://api.w-api.app/v1/instance/{INSTANCE_ID}/messages',
        f'https://api.w-api.app/v1/messages?instanceId={INSTANCE_ID}',
        f'https://api.w-api.app/v1/instance/{INSTANCE_ID}/chats',
        f'https://api.w-api.app/v1/chats?instanceId={INSTANCE_ID}',
        f'https://api.w-api.app/v1/instance/{INSTANCE_ID}/history',
        f'https://api.w-api.app/v1/webhook/messages?instanceId={INSTANCE_ID}'
    ]

    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }

    for i, url in enumerate(endpoints, 1):
        print(f"\n🔍 Testando endpoint {i}: {url}")

        try:
            response = requests.get(url, headers=headers)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print("✅ SUCESSO! Dados encontrados:")
                    print(data)

                    return url, data
                except:
                    print("✅ Resposta 200, mas não é JSON válido")
                    print(response.text[:200])
            else:
                print(f"❌ Erro: {response.text[:100]}")

        except Exception as e:
            print(f"❌ Erro na requisição: {e}")

    print("\n❌ Nenhum endpoint de busca funcionou")
    return None, None


def main():
    print("🤖 BUSCADOR DE MENSAGENS W-API")
    print("=" * 40)
    print("Com base no JSON que você mostrou, posso:")
    print("1 - Buscar mensagens do webhook.site")
    print("2 - Tentar buscar direto da API")
    print("3 - Mostrar formato da mensagem")

    opcao = input("\nEscolha uma opção (1-3): ").strip()

    if opcao == '1':
        print("\n📋 Para buscar do webhook.site:")
        print("1. Vá em webhook.site")
        print("2. Copie o ID da sua URL (a parte depois de webhook.site/)")
        print("3. Cole aqui")
        buscar_mensagens_webhook()

    elif opcao == '2':
        url_funcionando, dados = buscar_via_api()

        if url_funcionando:
            print(f"\n✅ Endpoint funcionando: {url_funcionando}")
            continuar = input("Monitorar este endpoint? (s/n): ").lower()

            if continuar == 's':
                print("🔄 Monitorando... Pressione Ctrl+C para parar")

                headers = {
                    'Authorization': f'Bearer {TOKEN}',
                    'Content-Type': 'application/json'
                }

                while True:
                    try:
                        response = requests.get(url_funcionando, headers=headers)
                        if response.status_code == 200:
                            data = response.json()
                            print(f"📊 {datetime.now().strftime('%H:%M:%S')} - Dados: {data}")
                        time.sleep(5)
                    except KeyboardInterrupt:
                        print("\n👋 Monitoramento parado!")
                        break

    elif opcao == '3':
        print("\n📋 FORMATO DA MENSAGEM RECEBIDA:")
        print("=" * 40)
        exemplo = {
            "event": "webhookReceived",
            "messageId": "ID_DA_MENSAGEM",
            "sender": {
                "pushName": "Nome do remetente",
                "id": "5569999267344"
            },
            "msgContent": {
                "conversation": "Texto da mensagem"
            },
            "moment": "timestamp",
            "isGroup": False,
            "fromMe": False
        }

        import json
        print(json.dumps(exemplo, indent=2, ensure_ascii=False))

    else:
        print("❌ Opção inválida!")


if __name__ == '__main__':
    main()


"""
{
  "event": "webhookReceived",
  "instanceId": "3B6XIW-ZTS923-GEAY6V",
  "connectedPhone": "556993291093",
  "isGroup": false,
  "messageId": "876A6DD9A41B758E8173C5636C810B17",
  "fromMe": false,
  "chat": {
    "id": "556999267344",
    "profilePicture": "https://pps.whatsapp.net/v/t61.24694-24/462429652_2229319410767469_7773187573644695635_n.jpg?ccb=11-4&oh=01_Q5Aa1gG5lzoU2UWKiXhyHIYGy7hfH-eOQOM9o0LgkMT9A09Khg&oe=684B056F&_nc_sid=5e03e0&_nc_cat=100"
  },
  "sender": {
    "id": "556999267344",
    "profilePicture": "https://pps.whatsapp.net/v/t61.24694-24/462429652_2229319410767469_7773187573644695635_n.jpg?ccb=11-4&oh=01_Q5Aa1gG5lzoU2UWKiXhyHIYGy7hfH-eOQOM9o0LgkMT9A09Khg&oe=684B056F&_nc_sid=5e03e0&_nc_cat=100",
    "pushName": "",
    "verifiedBizName": ""
  },
  "moment": 1748896286,
  "msgContent": {
    "imageMessage": {
      "url": "https://mmg.whatsapp.net/v/t62.7118-24/33415119_1109872547667460_6328002190673579716_n.enc?ccb=11-4&oh=01_Q5Aa1gH1SjkcBVnQeKJL71Je4KdTcAGvXwKt5BFRnmjky7hW0g&oe=68659116&_nc_sid=5e03e0&mms3=true",
      "mimetype": "image/jpeg",
      "fileSha256": "Pjic70EpZOCollw6/AdUWDfchPg1W5NOBcwyCSHEsi8=",
      "fileLength": "76970",
      "height": 1280,
      "width": 720,
      "mediaKey": "ZWyfNNPQQ5+oiCTLq+utoIOxyzv3GQvLe5nV+VwRZZA=",
      "fileEncSha256": "pQtHT6TXqO91WlgiFtP+lSqLMsfjSn/sd6yds8LUHdw=",
      "directPath": "/v/t62.7118-24/33415119_1109872547667460_6328002190673579716_n.enc?ccb=11-4&oh=01_Q5Aa1gH1SjkcBVnQeKJL71Je4KdTcAGvXwKt5BFRnmjky7hW0g&oe=68659116&_nc_sid=5e03e0",
      "mediaKeyTimestamp": "1748890765",
      "scansSidecar": "C4ZfPZoHeXznOK688W4aup/v4HEVd5ZFxNjnFGsKbA+AM3gsGQNdsw==",
      "scanLengths": [
        10294,
        30044,
        13840,
        22792
      ],
      "midQualityFileSha256": "xGgR8Llv62X6fdyYEuw12R3zExCUxC+Olex3QCcIPdI="
    }
  }
}
"""
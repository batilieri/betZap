#!/usr/bin/env python3
"""
Webhook com Ngrok - Token Configurado
Configura automaticamente o token e cria túnel
"""

from flask import Flask, request, jsonify
from pyngrok import conf, ngrok
import json
import time
import threading
from datetime import datetime
import requests

# SEU TOKEN DO NGROK
NGROK_TOKEN = "249wILexYz7XZWEYPPd4ECjyzzr_2Q8e91e1G9EYEsEtNxNsa"


class WebhookNgrokConfigurado:
    def __init__(self, porta=5000):
        self.porta = porta
        self.app = Flask(__name__)
        self.requisicoes = []
        self.ngrok_url = None
        self.tunnel = None
        self.configurar_rotas()

    def configurar_rotas(self):
        """Configura as rotas do Flask"""

        @self.app.route('/webhook', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
        def webhook():
            """Endpoint principal do webhook"""
            dados = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'headers': dict(request.headers),
                'json': request.get_json(silent=True),
                'data': request.get_data(as_text=True),
                'args': dict(request.args),
                'form': dict(request.form),
                'content_type': request.content_type
            }

            self.requisicoes.append(dados)
            self.log_requisicao_completa(dados)

            return jsonify({
                'status': 'success',
                'message': 'Webhook recebido via Ngrok!',
                'timestamp': dados['timestamp'],
                'total': len(self.requisicoes),
                'ngrok_url': self.ngrok_url
            })

        @self.app.route('/status')
        def status():
            return jsonify({
                'status': 'online',
                'total_requisicoes': len(self.requisicoes),
                'ngrok_url': self.ngrok_url,
                'porta': self.porta,
                'tunnel_ativo': self.tunnel is not None
            })

        @self.app.route('/requisicoes')
        def listar_requisicoes():
            return jsonify({
                'total': len(self.requisicoes),
                'requisicoes': self.requisicoes[-10:]  # Últimas 10
            })

        @self.app.route('/limpar', methods=['POST'])
        def limpar():
            count = len(self.requisicoes)
            self.requisicoes.clear()
            return jsonify({
                'message': f'{count} requisições removidas',
                'novo_total': 0
            })

        @self.app.route('/')
        def home():
            return f"""
            <h1>🚀 Webhook Ngrok Funcionando!</h1>
            <p><strong>URL Pública:</strong> <a href="{self.ngrok_url}">{self.ngrok_url}</a></p>
            <p><strong>Total de requisições:</strong> {len(self.requisicoes)}</p>

            <h2>📋 Endpoints Disponíveis:</h2>
            <ul>
                <li><strong>Webhook:</strong> <code>{self.ngrok_url}/webhook</code></li>
                <li><strong>Status:</strong> <a href="{self.ngrok_url}/status">{self.ngrok_url}/status</a></li>
                <li><strong>Requisições:</strong> <a href="{self.ngrok_url}/requisicoes">{self.ngrok_url}/requisicoes</a></li>
                <li><strong>Limpar:</strong> <code>POST {self.ngrok_url}/limpar</code></li>
            </ul>

            <h2>🧪 Teste Rápido:</h2>
            <pre>
curl -X POST {self.ngrok_url}/webhook \\
  -H "Content-Type: application/json" \\
  -d '{{"mensagem": "teste", "timestamp": "{datetime.now().isoformat()}"}}'
            </pre>

            <h2>📱 Para WhatsApp Business API:</h2>
            <p>Use esta URL no webhook: <strong>{self.ngrok_url}/webhook</strong></p>
            """

    def log_requisicao_completa(self, dados):
        """Log detalhado da requisição"""
        print(f"\n🆕 NOVA REQUISIÇÃO - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)

        # Informações básicas
        print(f"📋 Método: {dados['method']}")
        print(f"🌐 IP: {dados['ip']}")
        print(f"📱 User-Agent: {dados['user_agent'][:100]}...")
        print(f"📦 Content-Type: {dados['content_type']}")

        # Analisar conteúdo principal
        print(f"\n💬 ANÁLISE DO CONTEÚDO:")

        conteudo_encontrado = False

        # JSON direto
        if dados['json']:
            print(f"✅ JSON encontrado:")
            print(json.dumps(dados['json'], indent=2, ensure_ascii=False))
            conteudo_encontrado = True

            # Verificar se é WhatsApp
            if self.detectar_whatsapp(dados['json']):
                self.processar_whatsapp(dados['json'])

        # Raw data
        elif dados['data']:
            print(f"📄 Raw data encontrado ({len(dados['data'])} chars):")
            print(f"   Conteúdo: {dados['data'][:500]}...")

            # Tentar converter para JSON
            try:
                json_data = json.loads(dados['data'])
                print(f"✅ JSON válido no raw data:")
                print(json.dumps(json_data, indent=2, ensure_ascii=False))

                if self.detectar_whatsapp(json_data):
                    self.processar_whatsapp(json_data)

                conteudo_encontrado = True
            except json.JSONDecodeError:
                print(f"📝 Texto simples (não é JSON)")
                conteudo_encontrado = True

        # Form data
        elif dados['form']:
            print(f"📝 Form data encontrado:")
            for key, value in dados['form'].items():
                print(f"   {key}: {value}")
            conteudo_encontrado = True

        # Query parameters
        elif dados['args']:
            print(f"❓ Query parameters:")
            for key, value in dados['args'].items():
                print(f"   {key}: {value}")
            conteudo_encontrado = True

        if not conteudo_encontrado:
            print(f"❌ Nenhum conteúdo encontrado")

        # Headers importantes
        print(f"\n🔧 HEADERS IMPORTANTES:")
        headers_importantes = [
            'Content-Type', 'Authorization', 'X-Webhook-Event',
            'X-GitHub-Event', 'X-Hub-Signature', 'User-Agent'
        ]

        for header in headers_importantes:
            if header in dados['headers']:
                valor = dados['headers'][header]
                if len(str(valor)) > 100:
                    valor = str(valor)[:100] + "..."
                print(f"   {header}: {valor}")

        print("=" * 60)

    def detectar_whatsapp(self, data):
        """Detecta se é mensagem do WhatsApp Business API"""
        if not isinstance(data, dict):
            return False

        # Campos comuns do WhatsApp Business API
        campos_whatsapp = [
            'object', 'entry', 'messages', 'changes',
            'event', 'instanceId', 'sender', 'chat',
            'msgContent', 'messageId', 'fromMe'
        ]

        encontrados = sum(1 for campo in campos_whatsapp if campo in data)

        # Verificar estrutura típica do WhatsApp
        if 'object' in data and data.get('object') == 'whatsapp_business_account':
            return True

        if 'entry' in data and isinstance(data['entry'], list):
            return True

        return encontrados >= 2

    def processar_whatsapp(self, data):
        """Processa mensagem específica do WhatsApp"""
        print(f"\n🎯 MENSAGEM WHATSAPP DETECTADA!")
        print("-" * 40)

        # WhatsApp Business API oficial
        if 'entry' in data:
            for entry in data.get('entry', []):
                if 'changes' in entry:
                    for change in entry['changes']:
                        if 'value' in change and 'messages' in change['value']:
                            for message in change['value']['messages']:
                                print(f"   📱 De: {message.get('from', 'N/A')}")
                                print(f"   📧 ID: {message.get('id', 'N/A')}")
                                print(f"   📝 Tipo: {message.get('type', 'N/A')}")

                                if 'text' in message:
                                    print(f"   💬 Texto: {message['text'].get('body', 'N/A')}")

                                if 'timestamp' in message:
                                    ts = datetime.fromtimestamp(int(message['timestamp']))
                                    print(f"   ⏰ Timestamp: {ts.strftime('%H:%M:%S')}")

        # Formato de outras APIs (W-API, etc.)
        else:
            campos_importantes = {
                'sender': 'Remetente',
                'chat': 'Chat',
                'msgContent': 'Conteúdo',
                'message': 'Mensagem',
                'messageId': 'ID da Mensagem',
                'fromMe': 'De mim',
                'isGroup': 'É grupo',
                'moment': 'Momento'
            }

            for campo, nome in campos_importantes.items():
                if campo in data:
                    valor = data[campo]
                    if isinstance(valor, dict):
                        if 'conversation' in valor:
                            valor = valor['conversation']
                        elif 'text' in valor:
                            valor = valor['text']
                    print(f"   {nome}: {valor}")

    def configurar_ngrok(self):
        """Configura o token do ngrok"""
        try:
            print("🔧 Configurando token do ngrok...")

            # Configurar token
            conf.get_default().auth_token = NGROK_TOKEN

            print("✅ Token configurado com sucesso!")
            return True

        except Exception as e:
            print(f"❌ Erro ao configurar ngrok: {e}")
            return False

    def criar_tunel_ngrok(self):
        """Cria túnel ngrok"""
        try:
            print(f"🚀 Criando túnel ngrok na porta {self.porta}...")

            # Criar túnel HTTP
            self.tunnel = ngrok.connect(self.porta, "http")
            self.ngrok_url = self.tunnel.public_url

            print(f"✅ Túnel ngrok criado!")
            print(f"🔗 URL pública: {self.ngrok_url}")
            print(f"📡 Webhook URL: {self.ngrok_url}/webhook")

            return True

        except Exception as e:
            print(f"❌ Erro ao criar túnel: {e}")
            return False

    def testar_webhook_completo(self):
        """Testa o webhook com diferentes tipos de requisição"""
        print(f"\n🧪 TESTANDO WEBHOOK COMPLETO...")
        print("-" * 40)

        testes = [
            {
                'nome': 'GET simples',
                'metodo': 'GET',
                'url': f"{self.ngrok_url}/webhook"
            },
            {
                'nome': 'POST JSON simples',
                'metodo': 'POST',
                'url': f"{self.ngrok_url}/webhook",
                'json': {
                    "teste": "webhook funcionando",
                    "timestamp": datetime.now().isoformat()
                }
            },
            {
                'nome': 'POST simulando WhatsApp',
                'metodo': 'POST',
                'url': f"{self.ngrok_url}/webhook",
                'json': {
                    "object": "whatsapp_business_account",
                    "entry": [{
                        "changes": [{
                            "value": {
                                "messages": [{
                                    "from": "5511999999999",
                                    "id": "test_msg_123",
                                    "type": "text",
                                    "text": {"body": "Olá! Teste do webhook"},
                                    "timestamp": str(int(time.time()))
                                }]
                            }
                        }]
                    }]
                }
            }
        ]

        for i, teste in enumerate(testes, 1):
            try:
                print(f"\n📡 Teste {i}: {teste['nome']}")

                if teste['metodo'] == 'GET':
                    response = requests.get(teste['url'], timeout=10)
                else:
                    response = requests.post(
                        teste['url'],
                        json=teste.get('json'),
                        timeout=10
                    )

                print(f"   ✅ Status: {response.status_code}")

                if response.status_code == 200:
                    resp_json = response.json()
                    print(f"   📊 Total requisições: {resp_json.get('total', 'N/A')}")

            except Exception as e:
                print(f"   ❌ Falhou: {e}")

    def parar_ngrok(self):
        """Para o túnel ngrok"""
        if self.tunnel:
            try:
                ngrok.disconnect(self.tunnel.public_url)
                print(f"🛑 Túnel ngrok fechado")
            except:
                pass

    def executar(self):
        """Executa o webhook completo"""
        print("🚀 WEBHOOK NGROK - CONFIGURAÇÃO AUTOMÁTICA")
        print("=" * 60)
        print("🔧 Configurando automaticamente seu token ngrok")
        print("🌐 Criando túnel público seguro")
        print("=" * 60)

        # 1. Configurar ngrok
        if not self.configurar_ngrok():
            print("❌ Falha na configuração. Verifique o token.")
            return

        # 2. Iniciar servidor Flask
        def iniciar_flask():
            self.app.run(host='127.0.0.1', port=self.porta, debug=False, use_reloader=False)

        thread_flask = threading.Thread(target=iniciar_flask, daemon=True)
        thread_flask.start()

        time.sleep(2)
        print(f"✅ Servidor Flask rodando na porta {self.porta}")

        # 3. Criar túnel
        if not self.criar_tunel_ngrok():
            print("❌ Falha ao criar túnel. Verifique sua conexão.")
            return

        # 4. Testar webhook
        self.testar_webhook_completo()

        # 5. Mostrar informações finais
        print(f"\n🎉 WEBHOOK FUNCIONANDO PERFEITAMENTE!")
        print("=" * 60)
        print(f"🔗 Webhook URL: {self.ngrok_url}/webhook")
        print(f"📊 Status URL: {self.ngrok_url}/status")
        print(f"🌐 Interface Web: {self.ngrok_url}")
        print(f"📋 Listar requisições: {self.ngrok_url}/requisicoes")
        print("=" * 60)
        print(f"💡 Use a URL do webhook em suas APIs")
        print(f"🔄 Monitorando requisições em tempo real...")
        print(f"💡 Pressione Ctrl+C para parar")
        print("=" * 60)

        # 6. Monitorar em tempo real
        try:
            contador = 0
            while True:
                total = len(self.requisicoes)
                if total > contador:
                    print(f"\n📈 Nova requisição recebida! Total: {total}")
                    contador = total

                print(f"\r🔍 Aguardando requisições... {datetime.now().strftime('%H:%M:%S')} | Total: {total}",
                      end="", flush=True)
                time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n\n👋 Encerrando webhook...")
            self.parar_ngrok()
            print(f"📊 Total de requisições processadas: {len(self.requisicoes)}")
            print(f"✅ Webhook encerrado com sucesso!")


def main():
    """Função principal"""
    print("🔍 WEBHOOK NGROK CONFIGURADO v1.0")
    print("=" * 50)
    print("🎯 Token já configurado automaticamente")
    print("🚀 Pronto para usar com WhatsApp Business API")
    print("=" * 50)

    # Verificar dependências
    try:
        import flask
        print("✅ Flask disponível")
    except ImportError:
        print("❌ Flask não encontrado! Execute: pip install flask")
        return

    try:
        import pyngrok
        print("✅ PyNgrok disponível")
    except ImportError:
        print("❌ PyNgrok não encontrado! Execute: pip install pyngrok")
        return

    try:
        webhook = WebhookNgrokConfigurado(porta=5000)
        webhook.executar()

    except KeyboardInterrupt:
        print("\n👋 Programa interrompido pelo usuário!")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

# ===============================================
# 🚀 WEBHOOK NGROK - RECURSOS:
# ===============================================
#
# ✅ Token configurado automaticamente
# ✅ Túnel HTTPS seguro
# ✅ Detecção avançada de WhatsApp
# ✅ Logs detalhados e organizados
# ✅ Interface web completa
# ✅ Testes automáticos
# ✅ Monitoramento em tempo real
# ✅ Múltiplos endpoints úteis
#
# ===============================================
# 📱 IDEAL PARA:
# ===============================================
#
# • WhatsApp Business API
# • Webhooks de pagamento
# • APIs de redes sociais
# • Testes de integração
# • Debug de requisições HTTP
#
# ===============================================
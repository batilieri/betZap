#!/usr/bin/env python3
"""
Servidor Webhook Melhorado para Interface WhatsApp
Versão otimizada para funcionar com a ui PyQt6
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import time
import threading
from datetime import datetime
import requests
import os


class WebhookServer:
    def __init__(self, porta=5000):
        self.porta = porta
        self.app = Flask(__name__)
        CORS(self.app)  # Permite CORS para requisições da ui
        self.requisicoes = []
        self.configurar_rotas()

    def configurar_rotas(self):
        """Configura as rotas do Flask"""

        @self.app.route('/webhook', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
        def webhook():
            """Endpoint principal do webhook"""
            dados = {
                'id': len(self.requisicoes) + 1,
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'headers': dict(request.headers),
                'json': request.get_json(silent=True),
                'data': request.get_data(as_text=True),
                'args': dict(request.args),
                'form': dict(request.form),
                'content_type': request.content_type,
                'url': request.url,
                'endpoint': request.endpoint
            }

            self.requisicoes.append(dados)
            self.log_requisicao_detalhada(dados)

            return jsonify({
                'status': 'success',
                'message': 'Webhook recebido com sucesso!',
                'timestamp': dados['timestamp'],
                'total': len(self.requisicoes),
                'id': dados['id']
            })

        @self.app.route('/status')
        def status():
            """Status do servidor"""
            return jsonify({
                'status': 'online',
                'servidor': 'Webhook Server v2.0',
                'total_requisicoes': len(self.requisicoes),
                'porta': self.porta,
                'timestamp': datetime.now().isoformat(),
                'uptime': time.time() - self.start_time if hasattr(self, 'start_time') else 0
            })

        @self.app.route('/requisicoes')
        def listar_requisicoes():
            """Lista todas as requisições"""
            return jsonify({
                'total': len(self.requisicoes),
                'requisicoes': self.requisicoes[-50:],  # Últimas 50
                'servidor': 'Webhook Server v2.0'
            })

        @self.app.route('/requisicoes/<int:req_id>')
        def obter_requisicao(req_id):
            """Obtém requisição específica por ID"""
            req = next((r for r in self.requisicoes if r['id'] == req_id), None)
            if req:
                return jsonify(req)
            return jsonify({'erro': 'Requisição não encontrada'}), 404

        @self.app.route('/limpar', methods=['POST'])
        def limpar():
            """Limpa todas as requisições"""
            count = len(self.requisicoes)
            self.requisicoes.clear()
            return jsonify({
                'message': f'{count} requisições removidas',
                'novo_total': 0,
                'timestamp': datetime.now().isoformat()
            })

        @self.app.route('/simular', methods=['POST'])
        def simular_mensagem():
            """Simula uma mensagem WhatsApp para teste"""
            dados_simulacao = {
                'object': 'whatsapp_business_account',
                'entry': [{
                    'id': '123456789',
                    'changes': [{
                        'value': {
                            'messaging_product': 'whatsapp',
                            'metadata': {
                                'display_phone_number': '5511999999999',
                                'phone_number_id': '123456789'
                            },
                            'messages': [{
                                'from': request.json.get('from', '5511987654321'),
                                'id': f'sim_{int(time.time())}',
                                'timestamp': str(int(time.time())),
                                'type': 'text',
                                'text': {
                                    'body': request.json.get('message', 'Mensagem de teste do webhook!')
                                }
                            }]
                        },
                        'field': 'messages'
                    }]
                }]
            }

            # Simula uma requisição POST no webhook
            with self.app.test_client() as client:
                response = client.post('/webhook',
                                       json=dados_simulacao,
                                       headers={'Content-Type': 'application/json'})

            return jsonify({
                'message': 'Mensagem simulada enviada!',
                'dados': dados_simulacao,
                'response': response.get_json()
            })

        @self.app.route('/test', methods=['GET', 'POST'])
        def teste_rapido():
            """Endpoint para testes rápidos"""
            if request.method == 'POST':
                return self.webhook()

            # GET - Página de teste
            html_teste = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Teste do Webhook</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .container { max-width: 600px; }
                    .form-group { margin: 15px 0; }
                    input, textarea, button { padding: 10px; margin: 5px 0; width: 100%; }
                    button { background: #25D366; color: white; border: none; cursor: pointer; }
                    button:hover { background: #128C7E; }
                    .response { background: #f5f5f5; padding: 15px; margin: 15px 0; }
                    .success { color: #25D366; }
                    .error { color: #d32f2f; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🧪 Teste do Webhook</h1>

                    <div class="form-group">
                        <h3>Simular Mensagem WhatsApp</h3>
                        <input type="text" id="from" placeholder="Número do remetente (ex: 5511987654321)" value="5511987654321">
                        <textarea id="message" placeholder="Digite a mensagem de teste" rows="3">Olá! Esta é uma mensagem de teste do webhook.</textarea>
                        <button onclick="simularWhatsApp()">📱 Enviar Mensagem WhatsApp</button>
                    </div>

                    <div class="form-group">
                        <h3>Teste JSON Personalizado</h3>
                        <textarea id="json" placeholder="Cole seu JSON aqui" rows="5">{"teste": "mensagem personalizada", "timestamp": "2024-01-01T12:00:00"}</textarea>
                        <button onclick="enviarJSON()">📨 Enviar JSON</button>
                    </div>

                    <div class="form-group">
                        <button onclick="verificarStatus()">📊 Verificar Status</button>
                        <button onclick="limparRequisicoes()">🗑️ Limpar Requisições</button>
                    </div>

                    <div id="response" class="response" style="display:none;">
                        <h4>Resposta:</h4>
                        <pre id="responseText"></pre>
                    </div>
                </div>

                <script>
                    function mostrarResposta(data, sucesso = true) {
                        const responseDiv = document.getElementById('response');
                        const responseText = document.getElementById('responseText');
                        responseText.textContent = JSON.stringify(data, null, 2);
                        responseDiv.style.display = 'block';
                        responseDiv.className = sucesso ? 'response success' : 'response error';
                    }

                    function simularWhatsApp() {
                        const from = document.getElementById('from').value;
                        const message = document.getElementById('message').value;

                        fetch('/simular', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({from: from, message: message})
                        })
                        .then(response => response.json())
                        .then(data => mostrarResposta(data))
                        .catch(error => mostrarResposta({erro: error.message}, false));
                    }

                    function enviarJSON() {
                        const jsonText = document.getElementById('json').value;

                        try {
                            const jsonData = JSON.parse(jsonText);
                            fetch('/webhook', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify(jsonData)
                            })
                            .then(response => response.json())
                            .then(data => mostrarResposta(data))
                            .catch(error => mostrarResposta({erro: error.message}, false));
                        } catch (e) {
                            mostrarResposta({erro: 'JSON inválido: ' + e.message}, false);
                        }
                    }

                    function verificarStatus() {
                        fetch('/status')
                        .then(response => response.json())
                        .then(data => mostrarResposta(data))
                        .catch(error => mostrarResposta({erro: error.message}, false));
                    }

                    function limparRequisicoes() {
                        fetch('/limpar', {method: 'POST'})
                        .then(response => response.json())
                        .then(data => mostrarResposta(data))
                        .catch(error => mostrarResposta({erro: error.message}, false));
                    }
                </script>
            </body>
            </html>
            """
            return html_teste

        @self.app.route('/')
        def home():
            """Página inicial do webhook"""
            total = len(self.requisicoes)
            ultima_requisicao = self.requisicoes[-1] if self.requisicoes else None

            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Webhook Server - Interface WhatsApp</title>
                <meta charset="utf-8">
                <style>
                    body {{ 
                        font-family: 'Segoe UI', Arial, sans-serif; 
                        margin: 0; 
                        padding: 20px; 
                        background: linear-gradient(135deg, #25D366, #128C7E);
                        min-height: 100vh;
                    }}
                    .container {{ 
                        max-width: 800px; 
                        margin: 0 auto; 
                        background: white; 
                        padding: 30px; 
                        border-radius: 15px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    }}
                    h1 {{ color: #25D366; text-align: center; }}
                    .status {{ 
                        background: #E8F5E8; 
                        padding: 15px; 
                        border-radius: 8px; 
                        margin: 20px 0;
                        border-left: 4px solid #25D366;
                    }}
                    .endpoints {{ 
                        background: #F5F5F5; 
                        padding: 20px; 
                        border-radius: 8px; 
                        margin: 20px 0;
                    }}
                    .endpoint {{ 
                        background: white; 
                        padding: 10px; 
                        margin: 10px 0; 
                        border-radius: 5px;
                        border: 1px solid #E0E0E0;
                    }}
                    .method {{ 
                        background: #25D366; 
                        color: white; 
                        padding: 3px 8px; 
                        border-radius: 3px; 
                        font-size: 12px;
                        margin-right: 10px;
                    }}
                    .url {{ font-family: monospace; color: #333; }}
                    .ultima {{ 
                        background: #FFF3E0; 
                        padding: 15px; 
                        border-radius: 8px; 
                        margin: 20px 0;
                        border-left: 4px solid #FF9800;
                    }}
                    .btn {{ 
                        display: inline-block; 
                        padding: 10px 20px; 
                        background: #25D366; 
                        color: white; 
                        text-decoration: none; 
                        border-radius: 5px; 
                        margin: 5px;
                    }}
                    .btn:hover {{ background: #128C7E; }}
                    pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 Webhook Server - Interface WhatsApp</h1>

                    <div class="status">
                        <h3>📊 Status do Servidor</h3>
                        <p><strong>Status:</strong> 🟢 Online</p>
                        <p><strong>Total de Requisições:</strong> {total}</p>
                        <p><strong>Porta:</strong> {self.porta}</p>
                        <p><strong>Timestamp:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    </div>

                    <div class="endpoints">
                        <h3>📋 Endpoints Disponíveis</h3>

                        <div class="endpoint">
                            <span class="method">POST</span>
                            <span class="url">http://localhost:{self.porta}/webhook</span>
                            <p>Endpoint principal para receber webhooks</p>
                        </div>

                        <div class="endpoint">
                            <span class="method">GET</span>
                            <span class="url">http://localhost:{self.porta}/status</span>
                            <p>Verificar status do servidor</p>
                        </div>

                        <div class="endpoint">
                            <span class="method">GET</span>
                            <span class="url">http://localhost:{self.porta}/requisicoes</span>
                            <p>Listar todas as requisições recebidas</p>
                        </div>

                        <div class="endpoint">
                            <span class="method">POST</span>
                            <span class="url">http://localhost:{self.porta}/limpar</span>
                            <p>Limpar todas as requisições</p>
                        </div>

                        <div class="endpoint">
                            <span class="method">POST</span>
                            <span class="url">http://localhost:{self.porta}/simular</span>
                            <p>Simular mensagem WhatsApp para teste</p>
                        </div>
                    </div>

                    <div>
                        <h3>🔗 Ações Rápidas</h3>
                        <a href="/test" class="btn">🧪 Página de Teste</a>
                        <a href="/status" class="btn">📊 Ver Status JSON</a>
                        <a href="/requisicoes" class="btn">📋 Ver Requisições</a>
                    </div>

                    {f'''
                    <div class="ultima">
                        <h3>📬 Última Requisição</h3>
                        <p><strong>Método:</strong> {ultima_requisicao["method"]}</p>
                        <p><strong>IP:</strong> {ultima_requisicao["ip"]}</p>
                        <p><strong>Timestamp:</strong> {ultima_requisicao["timestamp"]}</p>
                        <p><strong>Conteúdo:</strong></p>
                        <pre>{json.dumps(ultima_requisicao.get("json", ultima_requisicao.get("data", "Nenhum")), indent=2, ensure_ascii=False)[:300]}...</pre>
                    </div>
                    ''' if ultima_requisicao else '''
                    <div class="ultima">
                        <h3>📬 Nenhuma Requisição Recebida</h3>
                        <p>O servidor está aguardando requisições...</p>
                    </div>
                    '''}

                    <div class="endpoints">
                        <h3>💡 Como Usar com a Interface WhatsApp</h3>
                        <ol>
                            <li>Execute a ui WhatsApp: <code>python main_window.py</code></li>
                            <li>Na janela de configuração, digite: <code>http://localhost:{self.porta}</code></li>
                            <li>Clique em "Salvar e Conectar"</li>
                            <li>Use a <a href="/test">página de teste</a> para simular mensagens</li>
                            <li>As mensagens aparecerão automaticamente na ui</li>
                        </ol>
                    </div>
                </div>
            </body>
            </html>
            """

    def log_requisicao_detalhada(self, dados):
        """Log detalhado da requisição"""
        print(f"\n🆕 NOVA REQUISIÇÃO #{dados['id']} - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)

        print(f"📋 Método: {dados['method']}")
        print(f"🌐 IP: {dados['ip']}")
        print(f"📱 User-Agent: {dados['user_agent'][:50]}...")
        print(f"📦 Content-Type: {dados['content_type']}")

        # Analisar conteúdo
        print(f"\n💬 ANÁLISE DO CONTEÚDO:")

        if dados['json']:
            print(f"✅ JSON encontrado:")
            print(json.dumps(dados['json'], indent=2, ensure_ascii=False)[:500])

            # Detectar tipo de mensagem
            if self.detectar_whatsapp(dados['json']):
                print(f"🎯 MENSAGEM WHATSAPP DETECTADA!")
                self.processar_whatsapp_log(dados['json'])

        elif dados['data']:
            print(f"📄 Raw data encontrado ({len(dados['data'])} chars):")
            print(f"   Conteúdo: {dados['data'][:200]}...")

            try:
                json_data = json.loads(dados['data'])
                print(f"✅ JSON válido no raw data:")
                if self.detectar_whatsapp(json_data):
                    print(f"🎯 MENSAGEM WHATSAPP DETECTADA!")
                    self.processar_whatsapp_log(json_data)
            except:
                print(f"📝 Texto simples (não é JSON)")

        elif dados['form']:
            print(f"📝 Form data encontrado:")
            for key, value in dados['form'].items():
                print(f"   {key}: {value}")

        elif dados['args']:
            print(f"❓ Query parameters:")
            for key, value in dados['args'].items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ Nenhum conteúdo encontrado")

        print("=" * 60)

    def detectar_whatsapp(self, data):
        """Detecta se é mensagem do WhatsApp Business API"""
        if not isinstance(data, dict):
            return False

        # Campos do WhatsApp Business API
        campos_whatsapp = [
            'object', 'entry', 'messages', 'changes',
            'sender', 'chat', 'msgContent', 'messageId'
        ]

        encontrados = sum(1 for campo in campos_whatsapp if campo in data)

        # WhatsApp Business API oficial
        if 'object' in data and data.get('object') == 'whatsapp_business_account':
            return True

        if 'entry' in data and isinstance(data['entry'], list):
            return True

        return encontrados >= 2

    def processar_whatsapp_log(self, data):
        """Processa e exibe dados específicos do WhatsApp"""
        print("-" * 30)

        # WhatsApp Business API oficial
        if 'entry' in data:
            for entry in data.get('entry', []):
                if 'changes' in entry:
                    for change in entry['changes']:
                        value = change.get('value', {})
                        if 'messages' in value:
                            for message in value['messages']:
                                print(f"   📱 De: {message.get('from', 'N/A')}")
                                print(f"   📧 ID: {message.get('id', 'N/A')}")
                                print(f"   📝 Tipo: {message.get('type', 'N/A')}")

                                if 'text' in message:
                                    print(f"   💬 Texto: {message['text'].get('body', 'N/A')}")
                                elif 'image' in message:
                                    print(f"   📷 Imagem recebida")
                                elif 'audio' in message:
                                    print(f"   🎵 Áudio recebido")

                                if 'timestamp' in message:
                                    ts = datetime.fromtimestamp(int(message['timestamp']))
                                    print(f"   ⏰ Timestamp: {ts.strftime('%H:%M:%S')}")

        # Outros formatos (W-API, etc.)
        else:
            campos = {
                'sender': 'Remetente',
                'chat': 'Chat',
                'msgContent': 'Conteúdo',
                'messageId': 'ID da Mensagem',
                'fromMe': 'De mim'
            }

            for campo, nome in campos.items():
                if campo in data:
                    valor = data[campo]
                    if isinstance(valor, dict):
                        if 'conversation' in valor:
                            valor = valor['conversation']
                        elif 'text' in valor:
                            valor = valor['text']
                    print(f"   {nome}: {valor}")

    def executar(self):
        """Executa o servidor webhook"""
        self.start_time = time.time()

        print("🚀 SERVIDOR WEBHOOK - INTERFACE WHATSAPP")
        print("=" * 60)
        print(f"🌐 Servidor rodando em: http://localhost:{self.porta}")
        print(f"📡 Webhook URL: http://localhost:{self.porta}/webhook")
        print(f"🧪 Página de teste: http://localhost:{self.porta}/test")
        print(f"📊 Status: http://localhost:{self.porta}/status")
        print("=" * 60)
        print(f"💡 Use esta URL na ui WhatsApp: http://localhost:{self.porta}")
        print(f"🔄 Aguardando requisições...")
        print("=" * 60)

        try:
            self.app.run(
                host='0.0.0.0',  # Permite conexões externas
                port=self.porta,
                debug=False,
                use_reloader=False
            )
        except KeyboardInterrupt:
            print(f"\n👋 Servidor encerrado")
        except Exception as e:
            print(f"\n❌ Erro no servidor: {e}")


def testar_servidor():
    """Testa o servidor fazendo algumas requisições"""
    import time
    import requests

    print("🧪 TESTANDO SERVIDOR...")
    time.sleep(2)  # Aguarda servidor iniciar

    base_url = "http://localhost:5000"

    testes = [
        {
            'nome': 'Status do servidor',
            'url': f'{base_url}/status',
            'metodo': 'GET'
        },
        {
            'nome': 'Webhook simples',
            'url': f'{base_url}/webhook',
            'metodo': 'POST',
            'json': {'teste': 'webhook funcionando', 'timestamp': datetime.now().isoformat()}
        },
        {
            'nome': 'Simulação WhatsApp',
            'url': f'{base_url}/simular',
            'metodo': 'POST',
            'json': {'from': '5511987654321', 'message': 'Teste automático do servidor!'}
        }
    ]

    for teste in testes:
        try:
            print(f"\n📡 Testando: {teste['nome']}")

            if teste['metodo'] == 'GET':
                response = requests.get(teste['url'], timeout=5)
            else:
                response = requests.post(teste['url'], json=teste.get('json'), timeout=5)

            if response.status_code == 200:
                print(f"   ✅ Sucesso: {response.status_code}")
                data = response.json()
                if 'total' in data:
                    print(f"   📊 Total: {data['total']}")
            else:
                print(f"   ❌ Erro: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Falha: {e}")

    print(f"\n✅ Testes concluídos!")


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Servidor Webhook para Interface WhatsApp')
    parser.add_argument('--porta', '-p', type=int, default=5000,
                        help='Porta do servidor (padrão: 5000)')
    parser.add_argument('--teste', '-t', action='store_true',
                        help='Executar testes automáticos após iniciar')

    args = parser.parse_args()

    # Verifica dependências
    try:
        import flask
        print("✅ Flask disponível")
    except ImportError:
        print("❌ Flask não encontrado! Execute: pip install flask flask-cors")
        return

    try:
        servidor = WebhookServer(porta=args.porta)

        # Se solicitado, executa testes em thread separada
        if args.teste:
            thread_teste = threading.Thread(target=testar_servidor, daemon=True)
            thread_teste.start()

        servidor.executar()

    except KeyboardInterrupt:
        print("\n👋 Servidor interrompido pelo usuário!")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

# ===============================================
# 🚀 SERVIDOR WEBHOOK - RECURSOS:
# ===============================================
#
# ✅ Interface web completa com testes
# ✅ Detecção automática de WhatsApp Business API
# ✅ Simulação de mensagens para teste
# ✅ Logs detalhados e organizados
# ✅ CORS habilitado para ui PyQt6
# ✅ Múltiplos endpoints úteis
# ✅ Página de teste interativa
# ✅ Status em tempo real
# ✅ Compatível com ngrok
# ✅ Suporte a múltiplos formatos de API
#
# ===============================================
# 📱 COMO USAR:
# ===============================================
#
# 1. Execute o servidor:
#    python webhook_server.py
#
# 2. Execute a ui:
#    python main_window_ui.py
#
# 3. Na configuração, use:
#    http://localhost:5000
#
# 4. Teste na página:
#    http://localhost:5000/test
#
# ===============================================
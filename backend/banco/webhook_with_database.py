#!/usr/bin/env python3
"""
Cloudflare Tunnel Webhook Manager com Sistema de Banco de Dados
Versão integrada com salvamento automático em SQLite
"""

import subprocess
import threading
import time
import json
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import requests
import platform

# Importar nosso sistema de banco
from database_manager import WhatsAppDatabaseManager


class CloudflareWebhookManagerDB:
    """Gerenciador profissional do Cloudflare Tunnel com banco de dados"""

    def __init__(self, port=5000, db_path="whatsapp_webhook.db"):
        self.port = port
        self.db_path = db_path
        self.tunnel_url = None
        self.tunnel_process = None
        self.app = Flask(__name__)
        self.requests_log = []
        self.is_running = False

        # Inicializar banco de dados
        print(f"🗄️  Inicializando banco de dados: {db_path}")
        self.db_manager = WhatsAppDatabaseManager(db_path)
        print(f"✅ Banco de dados pronto!")

        # Configurar rotas do Flask
        self._setup_routes()

    def _setup_routes(self):
        """Configura as rotas do webhook"""

        @self.app.route('/webhook', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def webhook():
            """Endpoint principal do webhook"""
            request_data = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'url': request.url,
                'headers': dict(request.headers),
                'args': dict(request.args),
                'json': request.get_json(silent=True),
                'form': dict(request.form),
                'data': request.get_data(as_text=True)
            }

            # Salvar requisição no log temporário
            self.requests_log.append(request_data)

            # Se for webhook do WhatsApp, salvar no banco
            webhook_json = request.get_json(silent=True)
            if webhook_json and self._is_whatsapp_webhook(webhook_json):
                saved = self.db_manager.save_webhook_data(webhook_json)
                if saved:
                    print(f"💾 Dados salvos no banco de dados")
                else:
                    print(f"⚠️  Dados não salvos (possivelmente duplicados)")

            # Log no console
            print(f"\n📨 NOVA REQUISIÇÃO [{request.method}] - {datetime.now().strftime('%H:%M:%S')}")
            print(f"🔗 URL: {request.url}")
            if webhook_json:
                json_str = json.dumps(webhook_json, indent=2, ensure_ascii=False)
                print(f"📋 JSON: {json_str[:500]}{'...' if len(json_str) > 500 else ''}")

            return jsonify({
                'status': 'success',
                'message': 'Webhook recebido com sucesso',
                'timestamp': datetime.now().isoformat(),
                'saved_to_database': webhook_json and self._is_whatsapp_webhook(webhook_json)
            })

        @self.app.route('/requests', methods=['GET'])
        def get_requests():
            """Retorna todas as requisições capturadas"""
            return jsonify({
                'total': len(self.requests_log),
                'requests': self.requests_log
            })

        @self.app.route('/requests/clear', methods=['POST'])
        def clear_requests():
            """Limpa o log de requisições"""
            self.requests_log.clear()
            return jsonify({'message': 'Log limpo com sucesso'})

        @self.app.route('/status', methods=['GET'])
        def status():
            """Status do webhook"""
            db_info = self.db_manager.get_database_info()
            return jsonify({
                'status': 'online',
                'tunnel_url': self.tunnel_url,
                'port': self.port,
                'requests_count': len(self.requests_log),
                'database_info': db_info,
                'uptime': datetime.now().isoformat()
            })

        # === ROTAS DO BANCO DE DADOS ===

        @self.app.route('/db/messages', methods=['GET'])
        def get_messages():
            """Retorna mensagens do banco de dados"""
            limit = int(request.args.get('limit', 50))
            messages = self.db_manager.get_recent_messages(limit)
            return jsonify({
                'total': len(messages),
                'messages': messages
            })

        @self.app.route('/db/stats/daily', methods=['GET'])
        def get_daily_stats():
            """Retorna estatísticas diárias"""
            days = int(request.args.get('days', 7))
            stats = self.db_manager.get_daily_stats(days)
            return jsonify({
                'period_days': days,
                'stats': stats
            })

        @self.app.route('/db/stats/contacts', methods=['GET'])
        def get_contact_stats():
            """Retorna estatísticas de contatos"""
            limit = int(request.args.get('limit', 20))
            contacts = self.db_manager.get_contact_stats(limit)
            return jsonify({
                'total': len(contacts),
                'contacts': contacts
            })

        @self.app.route('/db/search', methods=['GET'])
        def search_messages():
            """Busca mensagens com filtros"""
            text = request.args.get('text')
            contact_id = request.args.get('contact_id')
            message_type = request.args.get('message_type')
            from_me = request.args.get('from_me')
            is_group = request.args.get('is_group')
            days_back = int(request.args.get('days_back', 30))
            limit = int(request.args.get('limit', 100))

            # Converter strings para boolean
            if from_me is not None:
                from_me = from_me.lower() == 'true'
            if is_group is not None:
                is_group = is_group.lower() == 'true'

            messages = self.db_manager.search_messages(
                text=text,
                contact_id=contact_id,
                message_type=message_type,
                from_me=from_me,
                is_group=is_group,
                days_back=days_back,
                limit=limit
            )

            return jsonify({
                'total': len(messages),
                'filters': {
                    'text': text,
                    'contact_id': contact_id,
                    'message_type': message_type,
                    'from_me': from_me,
                    'is_group': is_group,
                    'days_back': days_back,
                    'limit': limit
                },
                'messages': messages
            })

        @self.app.route('/db/info', methods=['GET'])
        def get_db_info():
            """Informações detalhadas do banco"""
            return jsonify(self.db_manager.get_database_info())

    def _is_whatsapp_webhook(self, data):
        """Verifica se é um webhook válido do WhatsApp"""
        if not isinstance(data, dict):
            return False

        required_fields = ['event', 'instanceId', 'messageId']
        return all(field in data for field in required_fields)

    def check_cloudflared(self):
        """Verifica se cloudflared está instalado"""
        try:
            cmd = 'cloudflared.exe' if platform.system() == 'Windows' else 'cloudflared'
            result = subprocess.run([cmd, '--version'],
                                    capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False

    def install_guide(self):
        """Mostra guia de instalação"""
        system = platform.system()

        print("\n📦 CLOUDFLARED NÃO ENCONTRADO")
        print("=" * 40)

        if system == "Windows":
            print("🪟 WINDOWS:")
            print("1. Baixe: https://github.com/cloudflare/cloudflared/releases/latest")
            print("2. Procure: cloudflared-windows-amd64.exe")
            print("3. Renomeie para: cloudflared.exe")
            print("4. Coloque na pasta do script")

        elif system == "Linux":
            print("🐧 LINUX:")
            print("wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64")
            print("sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared")
            print("sudo chmod +x /usr/local/bin/cloudflared")

        elif system == "Darwin":
            print("🍎 MACOS:")
            print("brew install cloudflared")

        print("\n🔄 Execute o script novamente após instalar")

    def create_tunnel(self):
        """Cria o túnel do Cloudflare"""
        if not self.check_cloudflared():
            self.install_guide()
            return False

        print(f"\n🚀 CRIANDO TÚNEL...")
        print(f"🔌 Porta local: {self.port}")

        try:
            cmd = 'cloudflared.exe' if platform.system() == 'Windows' else 'cloudflared'
            command = [cmd, 'tunnel', '--url', f'http://localhost:{self.port}']

            self.tunnel_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Aguardar URL do túnel
            timeout = 30
            start_time = time.time()

            while (time.time() - start_time) < timeout:
                line = self.tunnel_process.stdout.readline()

                if line and 'trycloudflare.com' in line:
                    words = line.split()
                    for word in words:
                        if 'https://' in word and 'trycloudflare.com' in word:
                            self.tunnel_url = word.strip()
                            print(f"✅ TÚNEL CRIADO: {self.tunnel_url}")
                            return True

                if self.tunnel_process.poll() is not None:
                    print("❌ Erro ao criar túnel")
                    return False

                time.sleep(0.5)

            print("❌ Timeout ao criar túnel")
            return False

        except Exception as e:
            print(f"❌ Erro: {e}")
            return False

    def start_webhook_server(self):
        """Inicia o servidor webhook"""
        print(f"\n🌐 INICIANDO SERVIDOR WEBHOOK...")
        print(f"📍 Porta: {self.port}")
        print(f"🗄️  Banco: {self.db_path}")

        # Iniciar Flask em thread separada
        def run_flask():
            self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)

        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()

        # Aguardar servidor iniciar
        time.sleep(2)

        try:
            response = requests.get(f'http://localhost:{self.port}/status', timeout=5)
            if response.status_code == 200:
                print("✅ Servidor webhook iniciado")
                return True
        except:
            pass

        print("❌ Erro ao iniciar servidor")
        return False

    def show_info(self):
        """Mostra informações do webhook"""
        if not self.tunnel_url:
            print("❌ Túnel não está ativo")
            return

        print("\n" + "=" * 70)
        print("🎉 WEBHOOK CLOUDFLARE + BANCO DE DADOS ATIVO!")
        print("=" * 70)
        print(f"🌐 URL Pública: {self.tunnel_url}")
        print(f"📨 Webhook: {self.tunnel_url}/webhook")
        print(f"🗄️  Banco: {self.db_path}")

        print(f"\n📊 ENDPOINTS DO BANCO:")
        print(f"• Mensagens: GET {self.tunnel_url}/db/messages?limit=100")
        print(f"• Stats diárias: GET {self.tunnel_url}/db/stats/daily?days=7")
        print(f"• Stats contatos: GET {self.tunnel_url}/db/stats/contacts?limit=20")
        print(f"• Buscar: GET {self.tunnel_url}/db/search?text=ola&days_back=30")
        print(f"• Info BD: GET {self.tunnel_url}/db/info")

        print(f"\n📋 ENDPOINTS BÁSICOS:")
        print(f"• Requisições: GET {self.tunnel_url}/requests")
        print(f"• Limpar log: POST {self.tunnel_url}/requests/clear")
        print(f"• Status: GET {self.tunnel_url}/status")

        print(f"\n🧪 TESTE RÁPIDO:")
        print(f"curl -X POST {self.tunnel_url}/webhook \\")
        print(f'  -H "Content-Type: application/json" \\')
        print(f'  -d \'{{"event": "test", "instanceId": "test", "messageId": "test123"}}\'')

        print("=" * 70)

    def monitor_requests(self):
        """Monitora requisições em tempo real"""
        print(f"\n📊 MONITORANDO WEBHOOKS + BANCO DE DADOS...")
        print(f"🔗 Webhook: {self.tunnel_url}/webhook")
        print(f"🗄️  Banco: {self.db_path}")
        print("💡 Pressione Ctrl+C para parar")
        print("-" * 50)

        last_count = 0
        last_db_count = 0

        try:
            while True:
                current_count = len(self.requests_log)

                # Verificar requisições
                if current_count > last_count:
                    print(f"📨 Nova requisição! Total: {current_count}")
                    if self.requests_log:
                        last_req = self.requests_log[-1]
                        print(f"   [{last_req['method']}] {last_req['timestamp']}")
                    last_count = current_count

                # Verificar banco de dados
                try:
                    db_info = self.db_manager.get_database_info()
                    current_db_count = db_info.get('total_events', 0)

                    if current_db_count > last_db_count:
                        print(f"💾 Nova mensagem no banco! Total: {current_db_count}")
                        print(f"   📊 Tamanho BD: {db_info.get('database_size_mb', 0)} MB")
                        last_db_count = current_db_count
                except Exception as e:
                    print(f"⚠️  Erro ao verificar BD: {e}")

                time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n👋 Monitoramento interrompido")

    def stop_tunnel(self):
        """Para o túnel"""
        if self.tunnel_process:
            print("\n🛑 Parando túnel...")
            self.tunnel_process.terminate()
            try:
                self.tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tunnel_process.kill()
            print("✅ Túnel parado")

        self.tunnel_process = None
        self.tunnel_url = None

    def run(self):
        """Executa o webhook manager completo"""
        print("☁️  CLOUDFLARE TUNNEL WEBHOOK + DATABASE MANAGER")
        print("=" * 60)

        # 1. Iniciar servidor webhook
        if not self.start_webhook_server():
            return False

        # 2. Criar túnel
        if not self.create_tunnel():
            return False

        # 3. Mostrar informações
        self.show_info()

        # 4. Monitorar
        try:
            self.monitor_requests()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_tunnel()

        return True


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Cloudflare Tunnel Webhook + Database Manager')
    parser.add_argument('--port', '-p', type=int, default=5000, help='Porta local (padrão: 5000)')
    parser.add_argument('--db', '-d', type=str, default="whatsapp_webhook.db",
                        help='Arquivo do banco (padrão: whatsapp_webhook.db)')
    args = parser.parse_args()

    manager = CloudflareWebhookManagerDB(port=args.port, db_path=args.db)

    try:
        manager.run()
    except KeyboardInterrupt:
        print(f"\n👋 Finalizando...")
        manager.stop_tunnel()


if __name__ == '__main__':
    main()

# =============================================================================
# 🚀 COMO USAR:
# =============================================================================
#
# 1. INSTALAR DEPENDÊNCIAS:
#    pip install flask requests sqlalchemy
#
# 2. EXECUTAR:
#    python webhook_with_database.py
#    ou
#    python webhook_with_database.py --port 8000 --db meu_banco.db
#
# 3. NOVOS ENDPOINTS DO BANCO:
#    • GET {url}/db/messages?limit=100 - Últimas mensagens
#    • GET {url}/db/stats/daily?days=7 - Estatísticas diárias
#    • GET {url}/db/stats/contacts?limit=20 - Top contatos
#    • GET {url}/db/search?text=ola&contact_id=556999267344 - Busca avançada
#    • GET {url}/db/info - Informações do banco
#
# 4. EXEMPLOS DE BUSCA:
#    • Buscar por texto: /db/search?text=bom%20dia
#    • Mensagens enviadas: /db/search?from_me=true
#    • Só grupos: /db/search?is_group=true
#    • Por contato: /db/search?contact_id=556999267344
#    • Só stickers: /db/search?message_type=sticker
#    • Últimos 7 dias: /db/search?days_back=7
#
# 5. BANCO DE DADOS:
#    • SQLite local (arquivo .db)
#    • Tabelas: webhook_events, chats, senders, message_contents, stats
#    • Indexado para busca rápida
#    • Backup automático do JSON original
#    • Estatísticas em tempo real
#
# =============================================================================
#!/usr/bin/env python3
"""
Cloudflare Tunnel Webhook Manager
Gerenciador profissional para criar túneis e capturar requisições de APIs
"""

import subprocess
import threading
import time
import json
from datetime import datetime
from flask import Flask, request, jsonify
import requests
import platform
import os


class CloudflareWebhookManager:
    """Gerenciador profissional do Cloudflare Tunnel para webhooks"""

    def __init__(self, port=5000):
        self.port = port
        self.tunnel_url = None
        self.tunnel_process = None
        self.app = Flask(__name__)
        self.requests_log = []
        self.is_running = False

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

            # Salvar requisição
            self.requests_log.append(request_data)

            # Log no console
            print(f"\n📨 NOVA REQUISIÇÃO [{request.method}] - {datetime.now().strftime('%H:%M:%S')}")
            print(f"🔗 URL: {request.url}")
            if request.get_json(silent=True):
                print(f"📋 JSON: {json.dumps(request.get_json(), indent=2)}")

            return jsonify({
                'status': 'success',
                'message': 'Webhook recebido com sucesso',
                'timestamp': datetime.now().isoformat()
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
            return jsonify({
                'status': 'online',
                'tunnel_url': self.tunnel_url,
                'port': self.port,
                'requests_count': len(self.requests_log),
                'uptime': datetime.now().isoformat()
            })

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
            print("2. Procure: cloudflared-ui-amd64.exe")
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

        print("\n" + "=" * 60)
        print("🎉 WEBHOOK CLOUDFLARE ATIVO!")
        print("=" * 60)
        print(f"🌐 URL Pública: {self.tunnel_url}")
        print(f"📨 Webhook: {self.tunnel_url}/webhook")
        print(f"📊 Requisições: {self.tunnel_url}/requests")
        print(f"🔍 Status: {self.tunnel_url}/status")

        print(f"\n🧪 TESTE RÁPIDO:")
        print(f"curl -X POST {self.tunnel_url}/webhook \\")
        print(f'  -H "Content-Type: application/json" \\')
        print(f'  -d \'{{"teste": "funcionando"}}\'')

        print(f"\n📋 COMANDOS:")
        print(f"• Ver requisições: GET {self.tunnel_url}/requests")
        print(f"• Limpar log: POST {self.tunnel_url}/requests/clear")
        print("=" * 60)

    def monitor_requests(self):
        """Monitora requisições em tempo real"""
        print(f"\n📊 MONITORANDO REQUISIÇÕES...")
        print(f"🔗 Webhook: {self.tunnel_url}/webhook")
        print("💡 Pressione Ctrl+C para parar")
        print("-" * 50)

        last_count = 0

        try:
            while True:
                current_count = len(self.requests_log)

                if current_count > last_count:
                    print(f"📨 Nova requisição! Total: {current_count}")
                    # Mostrar última requisição
                    if self.requests_log:
                        last_req = self.requests_log[-1]
                        print(f"   [{last_req['method']}] {last_req['timestamp']}")

                    last_count = current_count

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
        print("☁️  CLOUDFLARE TUNNEL WEBHOOK MANAGER")
        print("=" * 50)

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

    parser = argparse.ArgumentParser(description='Cloudflare Tunnel Webhook Manager')
    parser.add_argument('--port', '-p', type=int, default=5000, help='Porta local (padrão: 5000)')
    args = parser.parse_args()

    manager = CloudflareWebhookManager(port=args.port)

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
#    pip install flask requests
#
# 2. EXECUTAR:
#    python webhook_manager.py
#    ou
#    python webhook_manager.py --port 8000
#
# 3. ENDPOINTS DISPONÍVEIS:
#    • POST/GET {url}/webhook - Recebe dados da API
#    • GET {url}/requests - Lista todas requisições
#    • POST {url}/requests/clear - Limpa log
#    • GET {url}/status - Status do sistema
#
# 4. INTEGRAÇÃO COM SUA API:
#    - Use a URL do webhook como endpoint
#    - Todas requisições são automaticamente logadas
#    - Acesse /requests para ver os dados recebidos
#
# =============================================================================
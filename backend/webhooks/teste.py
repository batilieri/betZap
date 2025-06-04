#!/usr/bin/env python3
"""
Webhook com Serveo - Túnel SSH Gratuito
Alternativa ao ngrok que não precisa de autenticação
"""

from flask import Flask, request, jsonify
import json
import subprocess
import threading
import time
from datetime import datetime
import requests
import re


class WebhookServeo:
    def __init__(self, porta=5000):
        self.porta = porta
        self.app = Flask(__name__)
        self.requisicoes = []
        self.serveo_url = None
        self.processo_serveo = None
        self.configurar_rotas()

    def configurar_rotas(self):
        """Configura rotas do Flask"""

        @self.app.route('/webhook', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
        def webhook():
            dados = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'headers': dict(request.headers),
                'json': request.get_json(silent=True),
                'data': request.get_data(as_text=True),
                'args': dict(request.args),
                'form': dict(request.form)
            }

            self.requisicoes.append(dados)
            self.log_requisicao(dados)

            return jsonify({
                'status': 'success',
                'message': 'Webhook recebido via Serveo!',
                'timestamp': dados['timestamp'],
                'total': len(self.requisicoes)
            })

        @self.app.route('/status')
        def status():
            return jsonify({
                'status': 'online',
                'total_requisicoes': len(self.requisicoes),
                'serveo_url': self.serveo_url,
                'porta_local': self.porta
            })

    def log_requisicao(self, dados):
        """Log da requisição"""
        print(f"\n🆕 {dados['method']} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"🌐 IP: {dados['ip']}")

        if dados['json']:
            print("📦 JSON:")
            print(json.dumps(dados['json'], indent=2, ensure_ascii=False))
        elif dados['data']:
            print(f"📄 Data: {dados['data']}")
        elif dados['form']:
            print(f"📝 Form: {dados['form']}")

        print("-" * 40)

    def iniciar_serveo(self):
        """Inicia túnel Serveo via SSH"""
        print(f"🚀 Iniciando túnel Serveo...")

        try:
            # Comando SSH para criar túnel
            cmd = [
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ServerAliveInterval=60',
                '-R', f'80:localhost:{self.porta}',
                'serveo.net'
            ]

            # Iniciar processo em background
            self.processo_serveo = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Aguardar e capturar URL
            timeout = 15
            start_time = time.time()

            while time.time() - start_time < timeout:
                if self.processo_serveo.poll() is not None:
                    # Processo terminou, verificar erro
                    stderr = self.processo_serveo.stderr.read()
                    print(f"❌ Serveo falhou: {stderr}")
                    return False

                # Tentar ler stdout
                try:
                    line = self.processo_serveo.stdout.readline()
                    if line:
                        print(f"📡 Serveo: {line.strip()}")

                        # Procurar URL na saída
                        match = re.search(r'https://[a-zA-Z0-9]+\.serveo\.net', line)
                        if match:
                            self.serveo_url = match.group(0)
                            print(f"✅ Túnel Serveo criado!")
                            print(f"🔗 URL: {self.serveo_url}")
                            return True

                except:
                    pass

                time.sleep(0.5)

            print(f"⏰ Timeout ao obter URL do Serveo")
            return False

        except FileNotFoundError:
            print(f"❌ SSH não encontrado!")
            print(f"💡 No Windows: instale Git Bash ou OpenSSH")
            print(f"💡 No Linux/Mac: sudo apt install openssh-client")
            return False
        except Exception as e:
            print(f"❌ Erro ao iniciar Serveo: {e}")
            return False

    def parar_serveo(self):
        """Para o túnel Serveo"""
        if self.processo_serveo:
            try:
                self.processo_serveo.terminate()
                self.processo_serveo.wait(timeout=5)
                print(f"🛑 Túnel Serveo fechado")
            except:
                self.processo_serveo.kill()

    def testar_webhook(self):
        """Testa o webhook via Serveo"""
        if not self.serveo_url:
            return

        print(f"\n🧪 TESTANDO WEBHOOK...")

        try:
            # Teste GET
            response = requests.get(f"{self.serveo_url}/webhook", timeout=10)
            print(f"✅ GET: Status {response.status_code}")

            # Teste POST
            dados_teste = {
                "tipo": "teste_serveo",
                "mensagem": "Teste via túnel Serveo",
                "timestamp": datetime.now().isoformat()
            }

            response = requests.post(
                f"{self.serveo_url}/webhook",
                json=dados_teste,
                timeout=10
            )
            print(f"✅ POST: Status {response.status_code}")

        except Exception as e:
            print(f"❌ Teste falhou: {e}")

    def executar(self):
        """Executa webhook com Serveo"""
        print("🚀 WEBHOOK COM SERVEO")
        print("=" * 50)

        # Iniciar servidor Flask em thread
        def iniciar_flask():
            self.app.run(host='127.0.0.1', port=self.porta, debug=False)

        thread_flask = threading.Thread(target=iniciar_flask, daemon=True)
        thread_flask.start()

        # Aguardar Flask iniciar
        time.sleep(2)
        print(f"✅ Servidor Flask rodando na porta {self.porta}")

        # Iniciar túnel Serveo
        if not self.iniciar_serveo():
            print(f"❌ Falha ao criar túnel. Usando apenas localhost.")
            self.serveo_url = None

        # Testar se funcionou
        if self.serveo_url:
            self.testar_webhook()

            print(f"\n📋 URLS IMPORTANTES:")
            print(f"   🔗 Webhook: {self.serveo_url}/webhook")
            print(f"   📊 Status: {self.serveo_url}/status")
        else:
            print(f"\n📋 URL LOCAL:")
            print(f"   🔗 Webhook: http://localhost:{self.porta}/webhook")

        print(f"\n🔄 MONITORANDO...")
        print(f"💡 Pressione Ctrl+C para parar")
        print("=" * 50)

        try:
            contador = 0
            while True:
                total = len(self.requisicoes)
                if total > contador:
                    print(f"📈 Total: {total}")
                    contador = total

                print(f"\r🔍 Aguardando... {datetime.now().strftime('%H:%M:%S')}",
                      end="", flush=True)
                time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n\n👋 Encerrando...")
            self.parar_serveo()
            print(f"📊 Total processado: {len(self.requisicoes)}")


def main():
    """Função principal"""
    print("🔍 WEBHOOK SERVEO v1.0")
    print("=" * 40)
    print("🌐 Túnel SSH gratuito via serveo.net")
    print("🔓 Sem necessidade de autenticação")
    print("=" * 40)

    try:
        webhook = WebhookServeo(porta=5000)
        webhook.executar()

    except KeyboardInterrupt:
        print("\n👋 Programa interrompido!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")


if __name__ == '__main__':
    main()

# ===============================================
# 🌐 SERVEO.NET - CARACTERÍSTICAS:
# ===============================================
#
# ✅ Totalmente gratuito
# ✅ Sem necessidade de cadastro
# ✅ Usa SSH (disponível na maioria dos sistemas)
# ✅ URLs públicas https://
# ✅ Sem limite de tempo
#
# ===============================================
# 📋 REQUISITOS:
# ===============================================
#
# • SSH client instalado
# • Windows: Git Bash ou OpenSSH
# • Linux/Mac: openssh-client
# • Flask: pip install flask requests
#
# ===============================================
# 💡 COMO FUNCIONA:
# ===============================================
#
# 1. Cria túnel SSH para serveo.net
# 2. Serveo.net redireciona tráfego para localhost
# 3. Você recebe URL pública gratuita
# 4. Exemplo: https://abc123.serveo.net
#
# ===============================================
# https://dashboard.ngrok.com/get-started/your-authtoken

#!/usr/bin/env python3
"""
Túnel Gratuito para WhatsApp Webhook - Substituto do Ngrok
Criado especificamente para conectar APIs do WhatsApp com webhook local
"""

import json
import time
import threading
import subprocess
import signal
import sys
import os
import requests
from datetime import datetime
from flask import Flask, request, jsonify


class WhatsAppWebhookTunnel:
    """Túnel específico para WhatsApp sem ngrok"""

    def __init__(self, porta_local=5000, token_verificacao="TOKEN_VERIFICACAO_WHATSAPP"):
        self.porta_local = porta_local
        self.token_verificacao = token_verificacao
        self.app = Flask(__name__)
        self.url_publica = None
        self.processo_tunnel = None
        self.servidor_ativo = False

        # Histórico de mensagens
        self.mensagens_recebidas = []
        self.stats = {
            'total_mensagens': 0,
            'total_verificacoes': 0,
            'inicio': datetime.now(),
            'contatos_unicos': set()
        }

        self.configurar_rotas_whatsapp()
        signal.signal(signal.SIGINT, self.encerrar)

    def configurar_rotas_whatsapp(self):
        """Configura rotas específicas para WhatsApp Business API"""

        @self.app.route('/webhook', methods=['GET'])
        def verificar_webhook():
            """Verificação do webhook do WhatsApp - OBRIGATÓRIO"""

            # Parâmetros de verificação do WhatsApp
            mode = request.args.get('hub.mode')
            token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')

            print(f"\n🔐 VERIFICAÇÃO WEBHOOK WHATSAPP:")
            print(f"   Mode: {mode}")
            print(f"   Token recebido: {token}")
            print(f"   Challenge: {challenge}")
            print(f"   Token esperado: {self.token_verificacao}")

            # Verificar se é uma verificação válida
            if mode == 'subscribe' and token == self.token_verificacao:
                print(f"✅ Verificação APROVADA!")
                print(f"   Respondendo com challenge: {challenge}")
                self.stats['total_verificacoes'] += 1

                # IMPORTANTE: Retornar o challenge como texto simples
                return challenge, 200, {'Content-Type': 'text/plain'}
            else:
                print(f"❌ Verificação REJEITADA!")
                print(f"   Motivo: Token incorreto ou mode inválido")
                return "Forbidden", 403

        @self.app.route('/webhook', methods=['POST'])
        def receber_mensagem_whatsapp():
            """Recebe mensagens do WhatsApp Business API"""

            dados = request.get_json()
            ip_origem = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

            print(f"\n📱 MENSAGEM WHATSAPP RECEBIDA:")
            print(f"   IP Origem: {ip_origem}")
            print(f"   Timestamp: {datetime.now().strftime('%H:%M:%S')}")
            print(f"   Dados completos:")
            print(json.dumps(dados, indent=2, ensure_ascii=False))

            # Processar mensagem
            if dados and 'entry' in dados:
                for entry in dados.get('entry', []):
                    self.processar_entry_whatsapp(entry)

            # Salvar histórico
            self.mensagens_recebidas.append({
                'timestamp': datetime.now().isoformat(),
                'ip_origem': ip_origem,
                'dados': dados
            })

            # Manter apenas últimas 100 mensagens
            if len(self.mensagens_recebidas) > 100:
                self.mensagens_recebidas = self.mensagens_recebidas[-100:]

            # Resposta obrigatória para o WhatsApp
            return jsonify({"status": "EVENT_RECEIVED"}), 200

        @self.app.route('/')
        def dashboard():
            """Dashboard para monitorar o webhook"""
            return self.gerar_dashboard_whatsapp()

        @self.app.route('/status')
        def status():
            """Status do webhook"""
            return jsonify({
                'status': 'online',
                'url_publica': self.url_publica,
                'porta_local': self.porta_local,
                'token_verificacao': self.token_verificacao,
                'stats': {
                    'total_mensagens': self.stats['total_mensagens'],
                    'total_verificacoes': self.stats['total_verificacoes'],
                    'contatos_unicos': len(self.stats['contatos_unicos']),
                    'tempo_ativo': str(datetime.now() - self.stats['inicio'])
                }
            })

        @self.app.route('/mensagens')
        def listar_mensagens():
            """Lista últimas mensagens recebidas"""
            return jsonify({
                'total': len(self.mensagens_recebidas),
                'mensagens': self.mensagens_recebidas[-20:]
            })

        @self.app.route('/test', methods=['GET', 'POST'])
        def testar_webhook():
            """Endpoint para testes"""
            if request.method == 'GET':
                return f"""
                <h1>🧪 Teste do Webhook WhatsApp</h1>
                <p><strong>URL Pública:</strong> {self.url_publica}</p>
                <p><strong>Webhook URL:</strong> {self.url_publica}/webhook</p>
                <p><strong>Token de Verificação:</strong> {self.token_verificacao}</p>

                <h2>Teste de Verificação:</h2>
                <pre>GET {self.url_publica}/webhook?hub.mode=subscribe&hub.verify_token={self.token_verificacao}&hub.challenge=TESTE123</pre>

                <h2>Teste de Mensagem:</h2>
                <form method="POST">
                    <textarea name="json" rows="10" cols="50">{{"entry": [{{"changes": [{{"value": {{"messages": [{{"from": "5511999999999", "text": {{"body": "Teste de mensagem"}}, "type": "text"}}]}}}}]}}]}}</textarea><br>
                    <button type="submit">Enviar Teste</button>
                </form>
                """
            else:
                json_data = request.form.get('json')
                try:
                    dados = json.loads(json_data)
                    return self.receber_mensagem_whatsapp()
                except:
                    return "Erro no JSON", 400

    def processar_entry_whatsapp(self, entry):
        """Processa uma entry do webhook do WhatsApp"""

        for change in entry.get('changes', []):
            value = change.get('value', {})

            # Processar mensagens
            if 'messages' in value:
                for message in value['messages']:
                    self.processar_mensagem_individual(message, value)

            # Processar status de entrega
            if 'statuses' in value:
                for status in value['statuses']:
                    self.processar_status_entrega(status)

    def processar_mensagem_individual(self, message, value):
        """Processa uma mensagem individual"""

        remetente = message.get('from')
        tipo = message.get('type')
        msg_id = message.get('id')
        timestamp = message.get('timestamp')

        # Adicionar às estatísticas
        self.stats['total_mensagens'] += 1
        self.stats['contatos_unicos'].add(remetente)

        print(f"\n💬 NOVA MENSAGEM:")
        print(f"   📞 De: {remetente}")
        print(f"   🆔 ID: {msg_id}")
        print(f"   📝 Tipo: {tipo}")
        print(f"   ⏰ Timestamp: {timestamp}")

        # Processar por tipo
        if tipo == 'text':
            texto = message.get('text', {}).get('body', '')
            print(f"   💭 Texto: {texto}")

        elif tipo == 'image':
            image_info = message.get('image', {})
            print(f"   🖼️ Imagem ID: {image_info.get('id')}")
            print(f"   📄 Mime: {image_info.get('mime_type')}")

        elif tipo == 'document':
            doc_info = message.get('document', {})
            print(f"   📎 Documento: {doc_info.get('filename')}")
            print(f"   📄 Mime: {doc_info.get('mime_type')}")

        elif tipo == 'audio':
            audio_info = message.get('audio', {})
            print(f"   🎵 Áudio ID: {audio_info.get('id')}")

        elif tipo == 'location':
            location = message.get('location', {})
            print(f"   📍 Localização: {location.get('latitude')}, {location.get('longitude')}")

        # Informações do perfil
        if 'contacts' in value:
            for contact in value['contacts']:
                if contact.get('wa_id') == remetente:
                    nome = contact.get('profile', {}).get('name', 'Sem nome')
                    print(f"   👤 Nome: {nome}")

        print("   " + "=" * 50)

    def processar_status_entrega(self, status):
        """Processa status de entrega de mensagens"""

        print(f"\n📋 STATUS DE ENTREGA:")
        print(f"   🆔 Message ID: {status.get('id')}")
        print(f"   📱 Para: {status.get('recipient_id')}")
        print(f"   ✅ Status: {status.get('status')}")
        print(f"   ⏰ Timestamp: {status.get('timestamp')}")

    def gerar_dashboard_whatsapp(self):
        """Gera dashboard específico para WhatsApp"""

        uptime = str(datetime.now() - self.stats['inicio']).split('.')[0]

        return f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>📱 WhatsApp Webhook Tunnel</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: Arial, sans-serif; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #25d366 0%, #128c7e 100%); 
                          color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                         gap: 20px; margin-bottom: 20px; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 8px; 
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
                .config {{ background: white; padding: 20px; border-radius: 8px; 
                          box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
                .messages {{ background: white; padding: 20px; border-radius: 8px; 
                           box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .message-item {{ border-left: 4px solid #25d366; padding: 15px; 
                               margin: 10px 0; background: #f8fff8; }}
                .status-online {{ color: #25d366; font-weight: bold; }}
                .url-box {{ background: #f8f9fa; padding: 15px; border-radius: 5px; 
                           border: 1px solid #dee2e6; margin: 10px 0; }}
                .btn {{ background: #25d366; color: white; padding: 10px 20px; 
                       border: none; border-radius: 5px; cursor: pointer; margin: 5px; 
                       text-decoration: none; display: inline-block; }}
                .btn:hover {{ background: #128c7e; }}
                pre {{ background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📱 WhatsApp Webhook Tunnel</h1>
                    <p class="status-online">● ONLINE</p>
                    <p>Substituto gratuito do ngrok para WhatsApp Business API</p>
                    <p>⏰ Ativo há: {uptime}</p>
                </div>

                <div class="stats">
                    <div class="stat-card">
                        <h3>💬 Mensagens</h3>
                        <h2>{self.stats['total_mensagens']}</h2>
                        <p>Total recebidas</p>
                    </div>
                    <div class="stat-card">
                        <h3>🔐 Verificações</h3>
                        <h2>{self.stats['total_verificacoes']}</h2>
                        <p>Webhook validado</p>
                    </div>
                    <div class="stat-card">
                        <h3>👥 Contatos</h3>
                        <h2>{len(self.stats['contatos_unicos'])}</h2>
                        <p>Únicos que enviaram</p>
                    </div>
                    <div class="stat-card">
                        <h3>🌐 Porta</h3>
                        <h2>{self.porta_local}</h2>
                        <p>Local</p>
                    </div>
                </div>

                <div class="config">
                    <h3>🔧 Configuração do Webhook</h3>

                    <h4>📡 URL do Webhook:</h4>
                    <div class="url-box">
                        <strong>{self.url_publica}/webhook</strong>
                    </div>

                    <h4>🔑 Token de Verificação:</h4>
                    <div class="url-box">
                        <strong>{self.token_verificacao}</strong>
                    </div>

                    <h4>📋 Cole essas informações na sua API do WhatsApp:</h4>
                    <ul style="margin: 15px 0; padding-left: 20px;">
                        <li><strong>URL do Webhook:</strong> {self.url_publica}/webhook</li>
                        <li><strong>Token de Verificação:</strong> {self.token_verificacao}</li>
                        <li><strong>Eventos:</strong> messages, message_deliveries</li>
                    </ul>

                    <div style="margin-top: 20px;">
                        <a href="/test" class="btn">🧪 Testar Webhook</a>
                        <a href="/status" class="btn">📊 Ver Status JSON</a>
                        <a href="/mensagens" class="btn">📱 Ver Mensagens JSON</a>
                        <button class="btn" onclick="location.reload()">🔄 Atualizar</button>
                    </div>
                </div>

                <div class="messages">
                    <h3>📱 Últimas Mensagens ({len(self.mensagens_recebidas)})</h3>

                    {self.gerar_lista_mensagens()}

                    {'' if self.mensagens_recebidas else '<p style="text-align: center; color: #666; margin: 30px 0;">Nenhuma mensagem recebida ainda. Configure o webhook na sua API do WhatsApp.</p>'}
                </div>
            </div>

            <script>
                // Auto-refresh a cada 10 segundos
                setTimeout(() => location.reload(), 10000);
            </script>
        </body>
        </html>
        """

    def gerar_lista_mensagens(self):
        """Gera HTML das últimas mensagens"""

        if not self.mensagens_recebidas:
            return ""

        html = ""
        for msg in self.mensagens_recebidas[-10:]:
            timestamp = msg['timestamp'].split('T')[1].split('.')[0]
            dados = msg['dados']

            # Extrair informações da mensagem
            info_msg = "Dados de webhook"
            if 'entry' in dados:
                for entry in dados['entry']:
                    for change in entry.get('changes', []):
                        if 'messages' in change.get('value', {}):
                            for message in change['value']['messages']:
                                remetente = message.get('from', 'Desconhecido')
                                tipo = message.get('type', 'unknown')

                                if tipo == 'text':
                                    texto = message.get('text', {}).get('body', '')
                                    info_msg = f"📱 {remetente}: {texto}"
                                else:
                                    info_msg = f"📱 {remetente}: [{tipo.upper()}]"

            html += f"""
            <div class="message-item">
                <div style="display: flex; justify-content: between; align-items: center;">
                    <div>
                        <strong>{info_msg}</strong><br>
                        <small>IP: {msg['ip_origem']} | {timestamp}</small>
                    </div>
                </div>
                <pre style="margin-top: 10px; max-height: 200px; overflow-y: auto;">{json.dumps(dados, indent=2, ensure_ascii=False)}</pre>
            </div>
            """

        return html

    # =================== MÉTODOS DE TÚNEL GRATUITO ===================

    def criar_tunnel_localtunnel(self):
        """Cria túnel usando LocalTunnel (melhor para WhatsApp)"""
        try:
            print("🔗 Criando túnel com LocalTunnel...")

            # Verificar se localtunnel está instalado
            try:
                subprocess.run(['which', 'lt'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print("📦 LocalTunnel não encontrado. Instalando...")
                try:
                    subprocess.run(['npm', 'install', '-g', 'localtunnel'], check=True)
                    print("✅ LocalTunnel instalado!")
                except subprocess.CalledProcessError:
                    print("❌ Erro ao instalar LocalTunnel. Instale Node.js primeiro:")
                    print("   https://nodejs.org/")
                    return False

            # Criar túnel
            print(f"🚀 Criando túnel para porta {self.porta_local}...")
            self.processo_tunnel = subprocess.Popen(
                ['lt', '--port', str(self.porta_local), '--subdomain', f'whatsapp-webhook-{int(time.time()) % 10000}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Aguardar e capturar URL
            time.sleep(5)

            # LocalTunnel mostra a URL no stdout
            if self.processo_tunnel.poll() is None:
                # Tentar capturar a URL do processo
                linha = self.processo_tunnel.stderr.readline().strip()
                if linha and 'https://' in linha:
                    self.url_publica = linha.split()[-1]
                else:
                    # URL padrão baseada no subdomain
                    subdomain = f'whatsapp-webhook-{int(time.time()) % 10000}'
                    self.url_publica = f'https://{subdomain}.loca.lt'

                print(f"✅ Túnel LocalTunnel ativo!")
                print(f"🌐 URL pública: {self.url_publica}")
                return True
            else:
                print("❌ Falha ao criar túnel LocalTunnel")
                return False

        except Exception as e:
            print(f"❌ Erro no LocalTunnel: {e}")
            return False

    def criar_tunnel_cloudflared(self):
        """Cria túnel usando Cloudflare Tunnel (grátis e rápido)"""
        try:
            print("🔗 Criando túnel com Cloudflare...")

            # Verificar se cloudflared está instalado
            try:
                subprocess.run(['cloudflared', '--version'], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("📦 Cloudflared não encontrado. Baixe em:")
                print(
                    "   https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
                return False

            # Criar túnel
            print(f"🚀 Criando túnel Cloudflare para porta {self.porta_local}...")
            self.processo_tunnel = subprocess.Popen(
                ['cloudflared', 'tunnel', '--url', f'http://localhost:{self.porta_local}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Aguardar URL
            for _ in range(30):  # Aguardar até 30 segundos
                if self.processo_tunnel.poll() is not None:
                    break

                linha = self.processo_tunnel.stdout.readline()
                if linha and 'trycloudflare.com' in linha:
                    # Extrair URL
                    parts = linha.split()
                    for part in parts:
                        if 'https://' in part and 'trycloudflare.com' in part:
                            self.url_publica = part.strip()
                            break

                    if self.url_publica:
                        print(f"✅ Túnel Cloudflare ativo!")
                        print(f"🌐 URL pública: {self.url_publica}")
                        return True

                time.sleep(1)

            print("❌ Não foi possível obter URL do Cloudflare")
            return False

        except Exception as e:
            print(f"❌ Erro no Cloudflare: {e}")
            return False

    def criar_tunnel_serveo(self):
        """Cria túnel usando Serveo (SSH)"""
        try:
            print("🔗 Criando túnel com Serveo...")

            # Gerar subdomínio único
            subdomain = f"whatsapp{int(time.time()) % 10000}"

            self.processo_tunnel = subprocess.Popen([
                'ssh', '-o', 'StrictHostKeyChecking=no',
                '-R', f'{subdomain}:80:localhost:{self.porta_local}',
                'serveo.net'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            time.sleep(8)
            if self.processo_tunnel.poll() is None:
                self.url_publica = f"https://{subdomain}.serveo.net"
                print(f"✅ Túnel Serveo ativo!")
                print(f"🌐 URL pública: {self.url_publica}")
                return True
            else:
                print("❌ Falha no túnel Serveo")
                return False

        except Exception as e:
            print(f"❌ Erro no Serveo: {e}")
            return False

    def executar(self, metodo_tunnel='auto'):
        """Executa o webhook com túnel"""

        print("📱 WHATSAPP WEBHOOK TUNNEL - SEM NGROK")
        print("=" * 60)
        print("🎯 Específico para WhatsApp Business API")
        print("🆓 100% Gratuito - Substituto do ngrok")
        print("=" * 60)

        # Iniciar servidor Flask em thread separada
        def iniciar_servidor():
            self.app.run(
                host='0.0.0.0',
                port=self.porta_local,
                debug=False,
                use_reloader=False,
                threaded=True
            )

        print(f"🚀 Iniciando servidor local na porta {self.porta_local}...")
        thread_servidor = threading.Thread(target=iniciar_servidor, daemon=True)
        thread_servidor.start()
        self.servidor_ativo = True

        time.sleep(3)
        print("✅ Servidor local ativo!")

        # Criar túnel baseado no método
        tunnel_criado = False

        if metodo_tunnel == 'auto':
            # Tentar métodos em ordem de preferência
            metodos = ['cloudflared', 'localtunnel', 'serveo']

            for metodo in metodos:
                print(f"\n🔄 Tentando {metodo}...")

                if metodo == 'cloudflared':
                    tunnel_criado = self.criar_tunnel_cloudflared()
                elif metodo == 'localtunnel':
                    tunnel_criado = self.criar_tunnel_localtunnel()
                elif metodo == 'serveo':
                    tunnel_criado = self.criar_tunnel_serveo()

                if tunnel_criado:
                    print(f"✅ Túnel criado com {metodo}!")
                    break
                else:
                    print(f"❌ Falha com {metodo}")

        else:
            # Método específico
            if metodo_tunnel == 'cloudflared':
                tunnel_criado = self.criar_tunnel_cloudflared()
            elif metodo_tunnel == 'localtunnel':
                tunnel_criado = self.criar_tunnel_localtunnel()
            elif metodo_tunnel == 'serveo':
                tunnel_criado = self.criar_tunnel_serveo()

        if not tunnel_criado:
            print("❌ Não foi possível criar túnel público!")
            print("💡 Executando apenas localmente...")
            self.url_publica = f"http://localhost:{self.porta_local}"

        # Mostrar informações finais
        self.mostrar_configuracao_final()

        # Monitorar
        self.monitorar_webhook()

    def mostrar_configuracao_final(self):
        """Mostra como configurar no WhatsApp"""

        print("\n" + "=" * 60)
        print("🎉 WEBHOOK WHATSAPP FUNCIONANDO!")
        print("=" * 60)
        print(f"🌐 URL Pública: {self.url_publica}")
        print(f"📡 Webhook URL: {self.url_publica}/webhook")
        print(f"🔑 Token Verificação: {self.token_verificacao}")
        print(f"🏠 Dashboard: {self.url_publica}")

        print(f"\n📋 CONFIGURAÇÃO NO WHATSAPP BUSINESS API:")
        print(f"   1. Acesse as configurações da sua API")
        print(f"   2. Na seção 'Configure webhooks':")
        print(f"      • URL do Webhook: {self.url_publica}/webhook")
        print(f"      • Token de Verificação: {self.token_verificacao}")
        print(f"      • Marque: messages, message_deliveries")
        print(f"   3. Clique em 'Salvar alterações'")

        print(f"\n🧪 TESTE MANUAL:")
        print(f"   Verificação:")
        print(
            f"   GET {self.url_publica}/webhook?hub.mode=subscribe&hub.verify_token={self.token_verificacao}&hub.challenge=TESTE123")

        print("\n💡 DICAS IMPORTANTES:")
        print("   • URL deve ser HTTPS (túneis já são HTTPS)")
        print("   • Token deve ser exatamente igual nos dois lados")
        print("   • WhatsApp testa a verificação antes de salvar")
        print("   • Mensagens aparecem aqui em tempo real")

        print("=" * 60)
        print("🔄 Aguardando verificação e mensagens do WhatsApp...")
        print("💡 Pressione Ctrl+C para parar")
        print("=" * 60)

    def monitorar_webhook(self):
        """Monitora o webhook em tempo real"""

        try:
            while self.servidor_ativo:
                total_msgs = len(self.mensagens_recebidas)
                verificacoes = self.stats['total_verificacoes']

                status = "🟢 ONLINE"
                if verificacoes == 0:
                    status = "🟡 AGUARDANDO VERIFICAÇÃO"
                elif total_msgs > 0:
                    status = "🟢 RECEBENDO MENSAGENS"

                print(
                    f"\r{status} | Verificações: {verificacoes} | Mensagens: {total_msgs} | {datetime.now().strftime('%H:%M:%S')}",
                    end="", flush=True)

                time.sleep(2)

        except KeyboardInterrupt:
            self.encerrar()

    def encerrar(self, signum=None, frame=None):
        """Encerra o webhook graciosamente"""

        print(f"\n\n👋 Encerrando WhatsApp Webhook Tunnel...")

        self.servidor_ativo = False

        if self.processo_tunnel:
            self.processo_tunnel.terminate()
            print("🔗 Túnel fechado")

        print(f"📊 Estatísticas finais:")
        print(f"   • Mensagens recebidas: {self.stats['total_mensagens']}")
        print(f"   • Verificações: {self.stats['total_verificacoes']}")
        print(f"   • Contatos únicos: {len(self.stats['contatos_unicos'])}")
        print(f"   • Tempo ativo: {datetime.now() - self.stats['inicio']}")
        print("✅ Encerrado com sucesso!")

        sys.exit(0)


def main():
    """Função principal com opções de configuração"""

    print("📱 WHATSAPP WEBHOOK TUNNEL v2.0")
    print("=" * 50)
    print("🆓 Substituto gratuito do ngrok para WhatsApp")
    print("=" * 50)

    # Configurar porta
    porta = input("Digite a porta local (padrão 5000): ").strip()
    if not porta:
        porta = 5000
    else:
        try:
            porta = int(porta)
        except ValueError:
            print("❌ Porta inválida, usando 5000")
            porta = 5000

    # Configurar token de verificação
    print(f"\n🔑 Configure o token de verificação:")
    print(f"   (Use o mesmo token na configuração do WhatsApp)")
    token = input("Token de verificação (padrão: MEU_TOKEN_WHATSAPP): ").strip()
    if not token:
        token = "MEU_TOKEN_WHATSAPP"

    # Escolher método de túnel
    print(f"\n🌐 Escolha o método de túnel:")
    print(f"1. 🚀 Automático (tenta todos até funcionar)")
    print(f"2. ☁️  Cloudflare Tunnel (mais rápido)")
    print(f"3. 🌐 LocalTunnel (via npm)")
    print(f"4. 🔗 Serveo (via SSH)")

    while True:
        escolha = input("Digite sua escolha (1-4): ").strip()
        if escolha == "1":
            metodo = "auto"
            break
        elif escolha == "2":
            metodo = "cloudflared"
            break
        elif escolha == "3":
            metodo = "localtunnel"
            break
        elif escolha == "4":
            metodo = "serveo"
            break
        else:
            print("❌ Opção inválida!")

    # Iniciar webhook
    try:
        webhook = WhatsAppWebhookTunnel(porta_local=porta, token_verificacao=token)
        webhook.executar(metodo_tunnel=metodo)

    except KeyboardInterrupt:
        print("\n👋 Programa interrompido pelo usuário!")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()


def exemplo_uso_simples():
    """Exemplo de uso mais simples"""

    # Configuração mínima
    webhook = WhatsAppWebhookTunnel(
        porta_local=5000,
        token_verificacao="MEU_TOKEN_SECRETO_123"
    )

    # Executar com túnel automático
    webhook.executar(metodo_tunnel='auto')


def instalar_dependencias():
    """Instala dependências necessárias"""

    print("📦 INSTALANDO DEPENDÊNCIAS...")
    print("=" * 40)

    # Dependências Python
    print("🐍 Instalando dependências Python...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'flask', 'requests'], check=True)
        print("✅ Flask e requests instalados!")
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar dependências Python")
        return False

    # Verificar Node.js para LocalTunnel
    print("\n📦 Verificando Node.js...")
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        print(f"✅ Node.js encontrado: {result.stdout.strip()}")

        # Instalar LocalTunnel
        print("🌐 Instalando LocalTunnel...")
        subprocess.run(['npm', 'install', '-g', 'localtunnel'], check=True)
        print("✅ LocalTunnel instalado!")

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Node.js não encontrado")
        print("   Para usar LocalTunnel, instale: https://nodejs.org/")

    # Verificar Cloudflared
    print("\n☁️  Verificando Cloudflare Tunnel...")
    try:
        result = subprocess.run(['cloudflared', '--version'], capture_output=True, text=True)
        print(f"✅ Cloudflared encontrado: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Cloudflared não encontrado")
        print(
            "   Para instalar: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")

    print("\n✅ Verificação de dependências concluída!")
    return True


def gerar_arquivo_docker():
    """Gera arquivos para executar no Docker"""

    dockerfile = '''FROM python:3.9-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \\
    curl \\
    openssh-client \\
    && rm -rf /var/lib/apt/lists/*

# Instalar Node.js e LocalTunnel
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \\
    && apt-get install -y nodejs \\
    && npm install -g localtunnel

# Instalar Cloudflared
RUN curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared \\
    && chmod +x /usr/local/bin/cloudflared

WORKDIR /app

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

EXPOSE 5000

CMD ["python", "whatsapp_webhook.py"]
'''

    requirements = '''flask==2.3.3
requests==2.31.0
'''

    docker_compose = '''version: '3.8'

services:
  whatsapp-webhook:
    build: .
    ports:
      - "5000:5000"
    environment:
      - WEBHOOK_TOKEN=SEU_TOKEN_AQUI
      - WEBHOOK_PORT=5000
    restart: unless-stopped
    stdin_open: true
    tty: true
'''

    # Criar arquivos
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)

    with open('requirements.txt', 'w') as f:
        f.write(requirements)

    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose)

    print("✅ Arquivos Docker criados:")
    print("   - Dockerfile")
    print("   - requirements.txt")
    print("   - docker-compose.yml")

    print("\n📚 Para usar:")
    print("   docker-compose up --build")


def gerar_script_install():
    """Gera script de instalação automática"""

    script = '''#!/bin/bash
# Script de instalação automática - WhatsApp Webhook Tunnel

echo "📱 Instalando WhatsApp Webhook Tunnel..."
echo "=================================="

# Atualizar sistema
echo "🔄 Atualizando sistema..."
sudo apt update

# Instalar Python e pip
echo "🐍 Instalando Python..."
sudo apt install -y python3 python3-pip

# Instalar dependências Python
echo "📦 Instalando dependências Python..."
pip3 install flask requests

# Instalar Node.js
echo "📦 Instalando Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Instalar LocalTunnel
echo "🌐 Instalando LocalTunnel..."
sudo npm install -g localtunnel

# Instalar Cloudflared (opcional)
echo "☁️  Instalando Cloudflare Tunnel..."
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared

echo "✅ Instalação concluída!"
echo "🚀 Para executar: python3 whatsapp_webhook.py"
'''

    with open('install.sh', 'w') as f:
        f.write(script)

    os.chmod('install.sh', 0o755)

    print("✅ Script de instalação criado: install.sh")
    print("📚 Para usar: chmod +x install.sh && ./install.sh")


def mostrar_guia_completo():
    """Mostra guia completo de configuração"""

    print("\n" + "=" * 60)
    print("📖 GUIA COMPLETO - WHATSAPP WEBHOOK TUNNEL")
    print("=" * 60)

    print("\n🎯 OBJETIVO:")
    print("   Substituir o ngrok para conectar WhatsApp Business API")
    print("   com webhook local, usando apenas ferramentas gratuitas.")

    print("\n📋 PRÉ-REQUISITOS:")
    print("   1. Python 3.6+ instalado")
    print("   2. Conta no WhatsApp Business API")
    print("   3. Uma das opções de túnel:")
    print("      • Node.js (para LocalTunnel)")
    print("      • Cloudflared (recomendado)")
    print("      • SSH (para Serveo)")

    print("\n🚀 INSTALAÇÃO RÁPIDA:")
    print("   # Instalar dependências:")
    print("   pip install flask requests")
    print("   ")
    print("   # Para LocalTunnel:")
    print("   npm install -g localtunnel")
    print("   ")
    print("   # Para Cloudflare (Linux):")
    print("   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64")
    print("   sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared")
    print("   sudo chmod +x /usr/local/bin/cloudflared")

    print("\n⚙️  CONFIGURAÇÃO NO WHATSAPP:")
    print("   1. Acesse Meta for Developers")
    print("   2. Vá para seu app > WhatsApp > Configuration")
    print("   3. Na seção 'Webhooks':")
    print("      • Callback URL: https://SEU-TUNNEL.com/webhook")
    print("      • Verify Token: MEU_TOKEN_SECRETO")
    print("      • Webhook fields: messages, message_deliveries")
    print("   4. Clique 'Verify and Save'")

    print("\n🔧 OPÇÕES DE TÚNEL:")
    print("   ")
    print("   🌟 CLOUDFLARE TUNNEL (Recomendado):")
    print("   • Mais rápido e estável")
    print("   • URLs com certificado SSL")
    print("   • Sem limite de tempo")
    print("   • Comando: cloudflared tunnel --url http://localhost:5000")
    print("   ")
    print("   🌐 LOCALTUNNEL:")
    print("   • Fácil de usar")
    print("   • Requer Node.js")
    print("   • URLs temporárias")
    print("   • Comando: lt --port 5000")
    print("   ")
    print("   🔗 SERVEO:")
    print("   • Usa SSH")
    print("   • Não precisa instalar nada")
    print("   • Comando: ssh -R 80:localhost:5000 serveo.net")

    print("\n🆓 ALTERNATIVAS PARA PRODUÇÃO:")
    print("   ")
    print("   ☁️  CLOUD GRÁTIS:")
    print("   • Heroku (500 horas/mês)")
    print("   • Railway (500 horas/mês)")
    print("   • Render (750 horas/mês)")
    print("   • Google Cloud Run (2M requests/mês)")
    print("   ")
    print("   🖥️  VPS GRÁTIS:")
    print("   • Oracle Cloud (Always Free)")
    print("   • Google Cloud (300$ créditos)")
    print("   • AWS (Free Tier 12 meses)")
    print("   • Azure (200$ créditos)")

    print("\n🔍 TROUBLESHOOTING:")
    print("   ")
    print("   ❌ 'Webhook verification failed':")
    print("   • Verifique se o token está idêntico")
    print("   • Confirme se a URL está acessível")
    print("   • Teste manualmente: GET /webhook?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=TESTE")
    print("   ")
    print("   ❌ 'Túnel não conecta':")
    print("   • Verifique firewall local")
    print("   • Teste outras opções de túnel")
    print("   • Confirme se a porta está livre")
    print("   ")
    print("   ❌ 'Mensagens não chegam':")
    print("   • Verificque se webhook foi validado")
    print("   • Confirme eventos marcados (messages)")
    print("   • Teste envio manual pelo Meta Developer")

    print("\n💡 DICAS IMPORTANTES:")
    print("   • URLs de túnel mudam a cada reinicialização")
    print("   • WhatsApp valida webhook antes de salvar")
    print("   • Use HTTPS sempre (túneis já fornecem)")
    print("   • Mantenha token seguro e único")
    print("   • Para produção, use serviços cloud")

    print("=" * 60)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        comando = sys.argv[1]

        if comando == 'install':
            instalar_dependencias()
        elif comando == 'docker':
            gerar_arquivo_docker()
        elif comando == 'script':
            gerar_script_install()
        elif comando == 'help':
            mostrar_guia_completo()
        elif comando == 'simple':
            exemplo_uso_simples()
        else:
            print("❌ Comando inválido!")
            print("Comandos disponíveis: install, docker, script, help, simple")
    else:
        main()

# =============================================================================
# 📱 WHATSAPP WEBHOOK TUNNEL - RECURSOS COMPLETOS:
# =============================================================================
#
# ✅ Substituto 100% gratuito do ngrok
# ✅ Múltiplas opções de túnel (Cloudflare, LocalTunnel, Serveo)
# ✅ Verificação automática do webhook WhatsApp
# ✅ Dashboard web em tempo real
# ✅ Processamento inteligente de mensagens
# ✅ Logs detalhados e organizados
# ✅ Suporte a todos os tipos de mídia WhatsApp
# ✅ Configuração simples e automática
# ✅ Monitoramento de estatísticas
# ✅ Preparado para produção
#
# =============================================================================
# 🆓 MÉTODOS DE TÚNEL GRATUITOS:
# =============================================================================
#
# 🌟 Cloudflare Tunnel - Mais rápido e confiável
# 🌐 LocalTunnel - Via npm, fácil instalação
# 🔗 Serveo - Via SSH, sem instalação
# ☁️  Cloud Run - Para produção (2M requests/mês)
# 🖥️  VPS Oracle - Always Free com IP fixo
#
# =============================================================================
# 📱 COMPATÍVEL COM:
# =============================================================================
#
# • WhatsApp Business API (Meta)
# • WhatsApp Cloud API
# • Baileys (WhatsApp Web JS)
# • Evolution API
# • Venom Bot
# • WPPConnect
# • Qualquer webhook que precise de HTTPS
#
# =============================================================================
# 🚀 COMANDOS RÁPIDOS:
# =============================================================================
#
# python whatsapp_webhook.py           # Executar com menu
# python whatsapp_webhook.py simple    # Executar configuração simples
# python whatsapp_webhook.py install   # Instalar dependências
# python whatsapp_webhook.py docker    # Gerar arquivos Docker
# python whatsapp_webhook.py help      # Mostrar ajuda completa
#
# =============================================================================
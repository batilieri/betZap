#!/usr/bin/env python3
"""
Cloudflare Tunnel Webhook Manager com Banco de Dados em Tempo Real
Sistema integrado para capturar, processar e salvar webhooks do WhatsApp
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

# Importar nosso sistema de banco atualizado
from database_manager_updated import WhatsAppDatabaseManager


class CloudflareWebhookRealtimeManager:
    """Gerenciador em tempo real do Cloudflare Tunnel com banco de dados"""

    def __init__(self, port=5000, db_path="whatsapp_webhook_realtime.db"):
        self.port = port
        self.db_path = db_path
        self.tunnel_url = None
        self.tunnel_process = None
        self.app = Flask(__name__)
        self.requests_log = []
        self.is_running = False
        self.webhook_count = 0
        self.last_webhook_time = None

        # Inicializar banco de dados
        print(f"🗄️  Inicializando banco de dados em tempo real: {db_path}")
        self.db_manager = WhatsAppDatabaseManager(db_path)
        print(f"✅ Sistema de banco pronto para processamento!")

        # Configurar rotas do Flask
        self._setup_routes()

    def _setup_routes(self):
        """Configura todas as rotas do webhook"""

        @self.app.route('/webhook', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def webhook():
            """Endpoint principal do webhook - PROCESSAMENTO EM TEMPO REAL"""
            start_time = time.time()

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

            # Salvar no log temporário
            self.requests_log.append(request_data)
            self.webhook_count += 1
            self.last_webhook_time = datetime.now()

            # Processar webhook do WhatsApp
            webhook_json = request.get_json(silent=True)
            saved_to_db = False
            error_message = None

            if webhook_json and self._is_whatsapp_webhook(webhook_json):
                try:
                    saved_to_db = self.db_manager.save_webhook_data(webhook_json)
                    if saved_to_db:
                        print(f"💾 ✅ Dados salvos no banco: {webhook_json.get('messageId', 'unknown')}")
                    else:
                        print(f"⚠️  Dados não salvos (duplicado): {webhook_json.get('messageId', 'unknown')}")
                except Exception as e:
                    error_message = str(e)
                    print(f"❌ Erro ao salvar no banco: {e}")

            # Log no console com detalhes
            processing_time = round((time.time() - start_time) * 1000, 2)
            print(
                f"\n📨 NOVA REQUISIÇÃO [#{self.webhook_count}] [{request.method}] - {datetime.now().strftime('%H:%M:%S')}")
            print(f"🔗 URL: {request.url}")
            print(f"⏱️  Processamento: {processing_time}ms")

            if webhook_json:
                # Detectar tipo de mensagem
                msg_type = self._detect_message_type(webhook_json)
                sender_name = webhook_json.get('sender', {}).get('pushName', 'Desconhecido')
                is_group = webhook_json.get('isGroup', False)
                from_me = webhook_json.get('fromMe', False)

                print(f"📋 Tipo: {msg_type} | De: {sender_name} | Grupo: {is_group} | Enviado: {from_me}")
                print(f"💾 Salvo no BD: {'✅' if saved_to_db else '❌'}")

                # Mostrar preview do conteúdo
                if msg_type == 'text':
                    text_content = webhook_json.get('msgContent', {}).get('conversation', '')
                    preview = text_content[:50] + '...' if len(text_content) > 50 else text_content
                    print(f"📝 Conteúdo: {preview}")
                elif msg_type == 'poll':
                    poll_name = webhook_json.get('msgContent', {}).get('pollCreationMessageV3', {}).get('name', '')
                    print(f"📊 Enquete: {poll_name}")

            return jsonify({
                'status': 'success',
                'message': 'Webhook processado com sucesso',
                'timestamp': datetime.now().isoformat(),
                'processing_time_ms': processing_time,
                'saved_to_database': saved_to_db,
                'webhook_count': self.webhook_count,
                'error': error_message
            })

        # === ROTAS DE STATUS E MONITORAMENTO ===

        @self.app.route('/status', methods=['GET'])
        def status():
            """Status detalhado do sistema"""
            db_info = self.db_manager.get_database_info()
            dashboard = self.db_manager.get_realtime_dashboard()

            return jsonify({
                'status': 'online',
                'tunnel_url': self.tunnel_url,
                'port': self.port,
                'webhook_count': self.webhook_count,
                'last_webhook': self.last_webhook_time.isoformat() if self.last_webhook_time else None,
                'database_info': db_info,
                'realtime_dashboard': dashboard,
                'uptime': datetime.now().isoformat(),
                'system_info': {
                    'platform': platform.system(),
                    'python_version': platform.python_version()
                }
            })

        @self.app.route('/dashboard', methods=['GET'])
        def dashboard():
            """Dashboard em tempo real"""
            try:
                dashboard_data = self.db_manager.get_realtime_dashboard()
                hourly_activity = self.db_manager.get_hourly_activity(7)
                daily_stats = self.db_manager.get_daily_stats(7)
                message_types = self.db_manager.get_message_types_summary()

                return jsonify({
                    'dashboard': dashboard_data,
                    'hourly_activity': hourly_activity,
                    'daily_stats': daily_stats,
                    'message_types': message_types,
                    'system': {
                        'total_webhooks_received': self.webhook_count,
                        'last_webhook': self.last_webhook_time.isoformat() if self.last_webhook_time else None,
                        'server_time': datetime.now().isoformat()
                    }
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # === ROTAS DO BANCO DE DADOS ===

        @self.app.route('/db/messages', methods=['GET'])
        def get_messages():
            """Retorna mensagens com informações detalhadas"""
            limit = min(int(request.args.get('limit', 50)), 500)  # Máximo 500
            messages = self.db_manager.get_recent_messages(limit)
            return jsonify({
                'total': len(messages),
                'limit': limit,
                'messages': messages
            })

        @self.app.route('/db/stats/daily', methods=['GET'])
        def get_daily_stats():
            """Estatísticas diárias"""
            days = min(int(request.args.get('days', 7)), 90)  # Máximo 90 dias
            stats = self.db_manager.get_daily_stats(days)
            return jsonify({
                'period_days': days,
                'stats': stats
            })

        @self.app.route('/db/stats/contacts', methods=['GET'])
        def get_contact_stats():
            """Estatísticas de contatos"""
            limit = min(int(request.args.get('limit', 20)), 100)  # Máximo 100
            contacts = self.db_manager.get_contact_stats(limit)
            return jsonify({
                'total': len(contacts),
                'limit': limit,
                'contacts': contacts
            })

        @self.app.route('/db/search', methods=['GET'])
        def search_messages():
            """Busca avançada de mensagens"""
            text = request.args.get('text')
            contact_id = request.args.get('contact_id')
            message_type = request.args.get('message_type')
            from_me = self._parse_bool(request.args.get('from_me'))
            is_group = self._parse_bool(request.args.get('is_group'))
            days_back = min(int(request.args.get('days_back', 30)), 365)  # Máximo 1 ano
            limit = min(int(request.args.get('limit', 100)), 500)  # Máximo 500

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

        @self.app.route('/db/types', methods=['GET'])
        def get_message_types():
            """Resumo dos tipos de mensagem"""
            return jsonify(self.db_manager.get_message_types_summary())

        @self.app.route('/db/activity/hourly', methods=['GET'])
        def get_hourly_activity():
            """Atividade por hora"""
            days = min(int(request.args.get('days', 7)), 30)
            activity = self.db_manager.get_hourly_activity(days)
            return jsonify({
                'days_analyzed': days,
                'hourly_activity': activity
            })

        @self.app.route('/db/info', methods=['GET'])
        def get_db_info():
            """Informações detalhadas do banco"""
            return jsonify(self.db_manager.get_database_info())

        # === ROTAS DE MANUTENÇÃO ===

        @self.app.route('/db/cleanup', methods=['POST'])
        def cleanup_database():
            """Limpeza de dados antigos"""
            days_to_keep = int(request.json.get('days_to_keep', 90))
            if days_to_keep < 7:
                return jsonify({'error': 'Mínimo 7 dias para manter'}), 400

            removed_count = self.db_manager.cleanup_old_data(days_to_keep)
            return jsonify({
                'message': f'Limpeza concluída',
                'removed_records': removed_count,
                'days_kept': days_to_keep
            })

        @self.app.route('/requests', methods=['GET'])
        def get_requests():
            """Log de requisições HTTP"""
            limit = min(int(request.args.get('limit', 100)), 1000)
            return jsonify({
                'total': len(self.requests_log),
                'showing': min(len(self.requests_log), limit),
                'requests': self.requests_log[-limit:] if self.requests_log else []
            })

        @self.app.route('/requests/clear', methods=['POST'])
        def clear_requests():
            """Limpa log de requisições"""
            cleared_count = len(self.requests_log)
            self.requests_log.clear()
            return jsonify({
                'message': 'Log de requisições limpo',
                'cleared_count': cleared_count
            })

    def _parse_bool(self, value):
        """Converte string para boolean"""
        if value is None:
            return None
        return value.lower() in ('true', '1', 'yes', 'on')

    def _is_whatsapp_webhook(self, data):
        """Verifica se é um webhook válido do WhatsApp"""
        if not isinstance(data, dict):
            return False

        required_fields = ['event', 'instanceId']
        return all(field in data for field in required_fields)

    def _detect_message_type(self, webhook_data):
        """Detecta o tipo da mensagem"""
        msg_content = webhook_data.get('msgContent', {})

        if 'conversation' in msg_content:
            return 'text'
        elif 'stickerMessage' in msg_content:
            return 'sticker'
        elif 'imageMessage' in msg_content:
            return 'image'
        elif 'videoMessage' in msg_content:
            return 'video'
        elif 'audioMessage' in msg_content:
            return 'audio'
        elif 'documentMessage' in msg_content:
            return 'document'
        elif 'locationMessage' in msg_content:
            return 'location'
        elif 'pollCreationMessageV3' in msg_content:
            return 'poll'
        else:
            return 'unknown'

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
        """Mostra guia de instalação do cloudflared"""
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

        print(f"\n🚀 CRIANDO TÚNEL CLOUDFLARE...")
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
        print(f"\n🌐 INICIANDO SERVIDOR WEBHOOK EM TEMPO REAL...")
        print(f"📍 Porta: {self.port}")
        print(f"🗄️  Banco: {self.db_path}")

        # Iniciar Flask em thread separada
        def run_flask():
            self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False, threaded=True)

        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()

        # Aguardar servidor iniciar
        time.sleep(3)

        try:
            response = requests.get(f'http://localhost:{self.port}/status', timeout=5)
            if response.status_code == 200:
                print("✅ Servidor webhook iniciado com sucesso")
                return True
        except Exception as e:
            print(f"❌ Erro ao verificar servidor: {e}")

        print("❌ Erro ao iniciar servidor")
        return False

    def show_info(self):
        """Mostra informações completas do sistema"""
        if not self.tunnel_url:
            print("❌ Túnel não está ativo")
            return

        print("\n" + "=" * 80)
        print("🎉 SISTEMA WEBHOOK + BANCO DE DADOS EM TEMPO REAL ATIVO!")
        print("=" * 80)
        print(f"🌐 URL Pública: {self.tunnel_url}")
        print(f"📨 Webhook Principal: {self.tunnel_url}/webhook")
        print(f"🗄️  Banco de Dados: {self.db_path}")

        print(f"\n📊 ENDPOINTS DO DASHBOARD:")
        print(f"• Status completo: GET {self.tunnel_url}/status")
        print(f"• Dashboard tempo real: GET {self.tunnel_url}/dashboard")

        print(f"\n💾 ENDPOINTS DO BANCO:")
        print(f"• Mensagens recentes: GET {self.tunnel_url}/db/messages?limit=50")
        print(f"• Stats diárias: GET {self.tunnel_url}/db/stats/daily?days=7")
        print(f"• Stats contatos: GET {self.tunnel_url}/db/stats/contacts?limit=20")
        print(f"• Tipos de mensagem: GET {self.tunnel_url}/db/types")
        print(f"• Atividade por hora: GET {self.tunnel_url}/db/activity/hourly?days=7")
        print(f"• Info do banco: GET {self.tunnel_url}/db/info")

        print(f"\n🔍 BUSCA AVANÇADA:")
        print(f"• Por texto: GET {self.tunnel_url}/db/search?text=ola")
        print(f"• Por contato: GET {self.tunnel_url}/db/search?contact_id=556999267344")
        print(f"• Por tipo: GET {self.tunnel_url}/db/search?message_type=sticker")
        print(f"• Mensagens enviadas: GET {self.tunnel_url}/db/search?from_me=true")
        print(f"• Só grupos: GET {self.tunnel_url}/db/search?is_group=true")

        print(f"\n🔧 MANUTENÇÃO:")
        print(f"• Limpar dados antigos: POST {self.tunnel_url}/db/cleanup")
        print(f"• Ver requisições: GET {self.tunnel_url}/requests?limit=100")
        print(f"• Limpar log: POST {self.tunnel_url}/requests/clear")

        print(f"\n🧪 TESTE RÁPIDO:")
        print(f"curl -X POST {self.tunnel_url}/webhook \\")
        print(f'  -H "Content-Type: application/json" \\')
        print(
            f'  -d \'{{"event": "webhookReceived", "instanceId": "test", "messageId": "test123", "msgContent": {{"conversation": "Teste de mensagem"}}}}\'')

        print("=" * 80)

    def monitor_realtime(self):
        """Monitor em tempo real com estatísticas avançadas"""
        print(f"\n📊 MONITORAMENTO EM TEMPO REAL ATIVADO")
        print(f"🔗 Webhook: {self.tunnel_url}/webhook")
        print(f"🗄️  Banco: {self.db_path}")
        print(f"📈 Dashboard: {self.tunnel_url}/dashboard")
        print("💡 Pressione Ctrl+C para parar")
        print("-" * 70)

        last_count = 0
        last_db_total = 0
        last_check = time.time()

        try:
            while True:
                current_time = time.time()

                # A cada 3 segundos, mostrar stats detalhadas
                if current_time - last_check >= 3:
                    try:
                        # Stats do webhook
                        current_count = self.webhook_count
                        webhooks_per_min = round((current_count - last_count) * 20,
                                                 1) if current_count > last_count else 0

                        # Stats do banco
                        db_info = self.db_manager.get_database_info()
                        current_db_total = db_info.get('total_events', 0)
                        db_growth = current_db_total - last_db_total

                        # Dashboard em tempo real
                        dashboard = self.db_manager.get_realtime_dashboard()
                        recent_messages = dashboard.get('recent_messages', [])

                        if current_count > last_count or db_growth > 0:
                            print(f"\n⚡ ATIVIDADE DETECTADA - {datetime.now().strftime('%H:%M:%S')}")
                            print(f"📨 Total webhooks: {current_count} (+{current_count - last_count})")
                            print(f"💾 Total no banco: {current_db_total} (+{db_growth})")
                            print(f"📊 Velocidade: {webhooks_per_min}/min")
                            print(f"💿 Tamanho BD: {db_info.get('database_size_mb', 0)} MB")

                            # Mostrar última mensagem se existir
                            if recent_messages:
                                last_msg = recent_messages[0]
                                sender_name = last_msg.get('sender', {}).get('pushName', 'Desconhecido')
                                msg_type = last_msg.get('_db_info', {}).get('message_type', 'unknown')
                                print(f"🔥 Última: {msg_type} de {sender_name}")

                            print("-" * 50)

                        last_count = current_count
                        last_db_total = current_db_total
                        last_check = current_time

                    except Exception as e:
                        print(f"⚠️  Erro no monitoramento: {e}")

                time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n👋 Monitoramento interrompido")
            self._show_final_stats()

    def _show_final_stats(self):
        """Mostra estatísticas finais ao parar"""
        try:
            print(f"\n📊 ESTATÍSTICAS FINAIS:")
            print("-" * 40)

            db_info = self.db_manager.get_database_info()
            dashboard = self.db_manager.get_realtime_dashboard()

            print(f"📨 Total webhooks recebidos: {self.webhook_count}")
            print(f"💾 Total mensagens no banco: {db_info.get('total_events', 0)}")
            print(f"📊 Tamanho do banco: {db_info.get('database_size_mb', 0)} MB")
            print(f"⏰ Primeira mensagem: {db_info.get('first_message_date', 'N/A')}")
            print(f"🕐 Última mensagem: {db_info.get('last_message_date', 'N/A')}")

            # Stats de hoje
            today_stats = db_info.get('today_stats', {})
            print(f"📅 Mensagens hoje: {today_stats.get('total_today', 0)}")
            print(f"📤 Enviadas hoje: {today_stats.get('sent_today', 0)}")
            print(f"📥 Recebidas hoje: {today_stats.get('received_today', 0)}")

            # Top tipos de mensagem
            types_summary = db_info.get('message_types', {})
            if types_summary.get('types'):
                print(f"\n📱 TIPOS DE MENSAGEM:")
                for msg_type, stats in types_summary['types'].items():
                    print(f"• {msg_type}: {stats['count']} ({stats['percentage']}%)")

        except Exception as e:
            print(f"⚠️  Erro ao mostrar stats finais: {e}")

    def stop_tunnel(self):
        """Para o túnel do Cloudflare"""
        if self.tunnel_process:
            print("\n🛑 Parando túnel Cloudflare...")
            self.tunnel_process.terminate()
            try:
                self.tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tunnel_process.kill()
            print("✅ Túnel parado")

        self.tunnel_process = None
        self.tunnel_url = None

    def run(self):
        """Executa o sistema completo"""
        print("☁️  CLOUDFLARE WEBHOOK + BANCO TEMPO REAL")
        print("=" * 60)

        # 1. Iniciar servidor webhook
        if not self.start_webhook_server():
            return False

        # 2. Criar túnel
        if not self.create_tunnel():
            return False

        # 3. Mostrar informações
        self.show_info()

        # 4. Monitorar em tempo real
        try:
            self.monitor_realtime()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_tunnel()

        return True


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Cloudflare Webhook + Database Realtime Manager')
    parser.add_argument('--port', '-p', type=int, default=5000,
                        help='Porta local (padrão: 5000)')
    parser.add_argument('--db', '-d', type=str, default="whatsapp_webhook_realtime.db",
                        help='Arquivo do banco (padrão: whatsapp_webhook_realtime.db)')
    args = parser.parse_args()

    manager = CloudflareWebhookRealtimeManager(port=args.port, db_path=args.db)

    try:
        manager.run()
    except KeyboardInterrupt:
        print(f"\n👋 Sistema finalizado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
    finally:
        manager.stop_tunnel()


if __name__ == '__main__':
    main()

    # =============================================================================
    # 🚀 SISTEMA WEBHOOK + BANCO DE DADOS EM TEMPO REAL
    # =============================================================================
    #
    # 📁 ARQUIVOS NECESSÁRIOS:
    # - models_updated.py (modelos do banco)
    # - database_manager_updated.py (gerenciador do banco)
    # - webhook_cloudflare_realtime.py (este arquivo - servidor principal)
    #
    # 🔧 INSTALAR DEPENDÊNCIAS:
    #    pip install flask requests sqlalchemy
    #
    # 🚀 EXECUTAR:
    #    python webhook_cloudflare_realtime.py
    #    python webhook_cloudflare_realtime.py --port 8000 --db meu_banco.db
    #
    # 📊 RECURSOS PRINCIPAIS:
    # - ✅ Processamento em tempo real de webhooks WhatsApp
    # - ✅ Salvamento automático no banco SQLite
    # - ✅ Suporte a todos os tipos: texto, sticker, imagem, vídeo, áudio, documento, localização, enquetes
    # - ✅ Dashboard em tempo real com estatísticas
    # - ✅ Busca avançada com filtros
    # - ✅ Monitoramento de atividade por hora/dia
    # - ✅ Limpeza automática de dados antigos
    # - ✅ Interface RESTful completa
    #
    # 🌐 ENDPOINTS PRINCIPAIS:
    # - POST/GET {url}/webhook - Recebe webhooks do WhatsApp
    # - GET {url}/dashboard - Dashboard completo em tempo real
    # - GET {url}/status - Status do sistema
    # - GET {url}/db/messages - Mensagens recentes
    # - GET {url}/db/search - Busca avançada
    # - GET {url}/db/stats/daily - Estatísticas diárias
    # - GET {url}/db/types - Resumo tipos de mensagem
    #
    # 🔍 EXEMPLOS DE USO:
    # - Buscar "olá": /db/search?text=olá
    # - Mensagens de um contato: /db/search?contact_id=556999267344
    # - Só stickers: /db/search?message_type=sticker
    # - Últimos 7 dias: /db/search?days_back=7
    # - Só grupos: /db/search?is_group=true
    # - Mensagens enviadas: /db/search?from_me=true
    #
    # 💾 BANCO DE DADOS:
    # - SQLite otimizado para performance
    # - Índices em campos importantes
    # - Cascata para exclusão
    # - Stats em tempo real
    # - Backup do JSON original
    #

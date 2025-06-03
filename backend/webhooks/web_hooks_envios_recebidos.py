#!/usr/bin/env python3
"""
Monitor Automático de WhatsApp - Versão Portável
Funciona em qualquer terminal/máquina com configuração flexível
"""

import requests
import json
import time
import os
import sys
from datetime import datetime


class MonitorPortavel:
    def __init__(self):
        self.webhook_id = None
        self.mensagens_processadas = set()
        self.contador_mensagens = 0
        self.ultima_verificacao = None
        self.config_file = "webhook_config.txt"

    def carregar_configuracao(self):
        """Carrega configuração salva ou solicita nova"""

        # 1. Verificar se foi passado como argumento
        if len(sys.argv) > 1:
            webhook_input = sys.argv[1]
            self.webhook_id = self.extrair_webhook_id(webhook_input)
            print(f"🔧 Webhook do argumento: {self.webhook_id}")
            return True

        # 2. Verificar variável de ambiente
        webhook_env = os.getenv('WEBHOOK_ID')
        if webhook_env:
            self.webhook_id = self.extrair_webhook_id(webhook_env)
            print(f"🔧 Webhook da variável de ambiente: {self.webhook_id}")
            return True

        # 3. Verificar arquivo de configuração
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    saved_webhook = f.read().strip()
                    if saved_webhook:
                        self.webhook_id = self.extrair_webhook_id(saved_webhook)
                        print(f"🔧 Webhook do arquivo salvo: {self.webhook_id}")

                        # Perguntar se quer usar o salvo
                        usar_salvo = input(f"\n❓ Usar webhook salvo? (s/n): ").lower()
                        if usar_salvo.startswith('s') or usar_salvo == '':
                            return True
            except:
                pass

        # 4. Solicitar novo webhook
        return self.solicitar_novo_webhook()

    def extrair_webhook_id(self, webhook_input):
        """Extrai o ID do webhook de diferentes formatos"""
        if not webhook_input:
            return None

        # Limpar URL completa se foi colada
        webhook_id = webhook_input.replace('https://webhook.site/', '')
        webhook_id = webhook_id.replace('http://webhook.site/', '')
        webhook_id = webhook_id.strip()

        return webhook_id if webhook_id else None

    def solicitar_novo_webhook(self):
        """Solicita novo webhook do usuário"""
        print("\n🔧 CONFIGURAR WEBHOOK")
        print("=" * 30)
        print("💡 Você pode fornecer:")
        print("1. URL completa: https://webhook.site/abc123...")
        print("2. Apenas o ID: abc123...")
        print("3. Deixar vazio para usar o padrão")

        webhook_input = input("\n🔗 Webhook: ").strip()

        if not webhook_input:
            # Usar webhook padrão
            self.webhook_id = "0e6e92fd-c357-44e4-b1e5-067d6ae4cd0d"
            print(f"✅ Usando webhook padrão: {self.webhook_id}")
        else:
            self.webhook_id = self.extrair_webhook_id(webhook_input)

        # Salvar configuração
        if self.webhook_id:
            self.salvar_configuracao()
            return True

        return False

    def salvar_configuracao(self):
        """Salva configuração para próxima execução"""
        try:
            with open(self.config_file, 'w') as f:
                f.write(self.webhook_id)
            print(f"💾 Configuração salva em {self.config_file}")
        except:
            print("⚠️ Não foi possível salvar a configuração")

    def testar_webhook(self):
        """Testa se o webhook está acessível"""
        try:
            url = f"https://webhook.site/token/{self.webhook_id}/requests"
            response = requests.get(url, timeout=1)

            if response.status_code == 200:
                print(f"✅ Webhook ativo e funcionando!")
                data = response.json()
                total_requests = len(data.get('data', []))
                print(f"📊 Total de requisições no webhook: {total_requests}")
                return True
            elif response.status_code == 404:
                print(f"❌ Webhook não encontrado ou expirado!")
                return False
            else:
                print(f"⚠️ Status do webhook: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Erro ao testar webhook: {e}")
            return False

    def buscar_mensagens_novas(self):
        """Busca mensagens novas no webhook"""
        try:
            url = f"https://webhook.site/token/{self.webhook_id}/requests"

            # Adicionar parâmetros para buscar apenas mensagens recentes
            params = {}
            if self.ultima_verificacao:
                params['since'] = self.ultima_verificacao.isoformat()

            response = requests.get(url, params=params, timeout=1)

            if response.status_code == 200:
                data = response.json()
                requests_data = data.get('data', [])

                mensagens_novas = []

                for request in requests_data:
                    request_id = request.get('uuid')

                    if request_id and request_id not in self.mensagens_processadas:
                        content = request.get('content')

                        if content and isinstance(content, str):
                            try:
                                message_data = json.loads(content)

                                # Verificar se é mensagem do WhatsApp
                                if self.eh_mensagem_whatsapp(message_data):
                                    mensagens_novas.append({
                                        'id': request_id,
                                        'data': message_data,
                                        'timestamp': request.get('created_at', '')
                                    })
                                    self.mensagens_processadas.add(request_id)

                            except json.JSONDecodeError:
                                pass

                self.ultima_verificacao = datetime.now()
                return mensagens_novas

            elif response.status_code == 404:
                print("❌ Webhook não encontrado ou expirado!")
                return None
            else:
                print(f"⚠️ Erro ao buscar mensagens: Status {response.status_code}")
                return []

        except requests.RequestException as e:
            print(f"🔄 Erro de conexão: {str(e)[:50]}...")
            return []
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return []

    def eh_mensagem_whatsapp(self, data):
        """Verifica se é uma mensagem válida do WhatsApp"""
        if isinstance(data, dict):
            return any([
                data.get('event') == 'webhookReceived',
                data.get('event') == 'message',
                data.get('type') == 'message',
                'instanceId' in data,
                'msgContent' in data,
                'sender' in data and 'chat' in data,
                'messages' in data,
                'entry' in data
            ])
        return False

    def processar_mensagem_whatsapp(self, data):
        """Processa e exibe mensagem do WhatsApp"""

        self.contador_mensagens += 1

        print('\n' + '🟢' * 70)
        print(f'📱 MENSAGEM #{self.contador_mensagens} - {datetime.now().strftime("%H:%M:%S")}')
        print('🟢' * 70)

        self.processar_formato_wapi(data)

        print('🟢' * 70 + '\n')

    def processar_formato_wapi(self, data):
        """Processa formato W-API"""

        # Informações básicas
        instance_id = data.get('instanceId', data.get('instance', 'N/A'))
        phone = data.get('connectedPhone', data.get('phone', 'N/A'))
        is_group = data.get('isGroup', False)
        from_me = data.get('fromMe', False)

        print(f"📞 Instância: {instance_id}")
        print(f"📱 Telefone: {phone}")
        print(f"{'👥 GRUPO' if is_group else '👤 PRIVADO'} | {'📤 ENVIADA' if from_me else '📥 RECEBIDA'}")

        # Informações do remetente
        sender = data.get('sender', {})
        if sender:
            sender_name = sender.get('pushName', sender.get('name', 'Sem nome'))
            sender_id = sender.get('id', sender.get('phone', 'N/A'))

            print(f"\n👤 DE: {sender_name}")
            print(f"📞 ID: {sender_id}")

            if sender.get('verifiedBizName'):
                print(f"🏢 Empresa: {sender.get('verifiedBizName')}")

        # Informações do chat
        chat = data.get('chat', {})
        if chat:
            chat_id = chat.get('id', 'N/A')
            print(f"💭 Chat ID: {chat_id}")

        # Processar conteúdo da mensagem
        self.processar_conteudo_mensagem(data)

        # Timestamp
        moment = data.get('moment', data.get('timestamp'))
        if moment:
            try:
                if isinstance(moment, (int, float)):
                    dt = datetime.fromtimestamp(moment)
                    print(f"\n🕐 Enviada em: {dt.strftime('%d/%m/%Y às %H:%M:%S')}")
            except:
                pass

        # ID da mensagem
        message_id = data.get('messageId', data.get('id', 'N/A'))
        print(f"🆔 ID: {message_id}")

    def processar_conteudo_mensagem(self, data):
        """Processa o conteúdo da mensagem"""

        msg_content = data.get('msgContent', data.get('message', data.get('content', {})))

        # Tentar campo 'text' diretamente
        if not msg_content and data.get('text'):
            print(f"\n💬 MENSAGEM:")
            print(f"📝 {data.get('text')}")
            return

        # Tentar campo 'body' diretamente  
        if not msg_content and data.get('body'):
            print(f"\n💬 MENSAGEM:")
            print(f"📝 {data.get('body')}")
            return

        if not msg_content:
            print(f"\n❓ DADOS BRUTOS:")
            print(f"📋 {json.dumps(data, indent=2, ensure_ascii=False)}")
            return

        # Processar diferentes tipos de conteúdo
        if isinstance(msg_content, str):
            print(f"\n💬 MENSAGEM:")
            print(f"📝 {msg_content}")

        elif isinstance(msg_content, dict):
            if 'conversation' in msg_content:
                print(f"\n💬 MENSAGEM:")
                print(f"📝 {msg_content['conversation']}")

            elif 'text' in msg_content:
                print(f"\n💬 MENSAGEM:")
                print(f"📝 {msg_content['text']}")

            elif 'messageStubType' in msg_content:
                stub_type = msg_content['messageStubType']
                print(f"\n⚙️ EVENTO DO SISTEMA: {stub_type}")

                eventos = {
                    'GROUP_PARTICIPANT_ADD': '🎉 Alguém foi adicionado ao grupo',
                    'GROUP_PARTICIPANT_REMOVE': '👋 Alguém foi removido do grupo',
                    'GROUP_PARTICIPANT_CHANGE_ROLE': '👑 Cargo alterado no grupo',
                    'GROUP_CHANGE_SUBJECT': '📝 Nome do grupo alterado',
                    'GROUP_CHANGE_DESCRIPTION': '📄 Descrição do grupo alterada'
                }

                if stub_type in eventos:
                    print(eventos[stub_type])

            elif 'imageMessage' in msg_content:
                print(f"\n🖼️ IMAGEM RECEBIDA")
                img_msg = msg_content['imageMessage']
                if img_msg.get('caption'):
                    print(f"📝 Legenda: {img_msg['caption']}")

            elif 'videoMessage' in msg_content:
                print(f"\n🎥 VÍDEO RECEBIDO")
                vid_msg = msg_content['videoMessage']
                if vid_msg.get('caption'):
                    print(f"📝 Legenda: {vid_msg['caption']}")

            elif 'audioMessage' in msg_content:
                print(f"\n🎵 ÁUDIO RECEBIDO")

            elif 'documentMessage' in msg_content:
                print(f"\n📄 DOCUMENTO RECEBIDO")
                doc_msg = msg_content['documentMessage']
                if doc_msg.get('fileName'):
                    print(f"📁 Arquivo: {doc_msg['fileName']}")

            else:
                print(f"\n❓ CONTEÚDO:")
                print(f"📋 {json.dumps(msg_content, indent=2, ensure_ascii=False)}")

    def monitorar_automatico(self):
        """Monitora o webhook automaticamente"""
        print(f"\n🚀 MONITORAMENTO AUTOMÁTICO INICIADO")
        print("=" * 50)
        print(f"🔗 Webhook: {self.webhook_id}")
        print("📱 Mensagens do WhatsApp aparecerão abaixo")
        print("💡 Pressione Ctrl+C para parar")
        print("🔄 Verificando a cada 3 segundos...\n")

        inicio = datetime.now()

        try:
            while True:
                mensagens_novas = self.buscar_mensagens_novas()

                if mensagens_novas is None:
                    break

                if mensagens_novas:
                    for msg in mensagens_novas:
                        self.processar_mensagem_whatsapp(msg['data'])

                # Status a cada 60 segundos
                tempo_ativo = datetime.now() - inicio
                if tempo_ativo.seconds % 60 == 0 and tempo_ativo.seconds > 0:
                    print(f"⏱️ Ativo há {tempo_ativo.seconds // 60}min | Mensagens: {self.contador_mensagens}")

                time.sleep(3)

        except KeyboardInterrupt:
            tempo_total = datetime.now() - inicio
            print(f"\n👋 MONITORAMENTO PARADO!")
            print(f"📊 Total de mensagens processadas: {self.contador_mensagens}")
            print(f"⏱️ Tempo total ativo: {tempo_total.seconds // 60}min {tempo_total.seconds % 60}s")

    def executar(self):
        """Executa o monitor"""
        print("🚀 MONITOR PORTÁVEL DE WHATSAPP")
        print("=" * 40)
        print("💡 Funciona em qualquer terminal/máquina!")

        if self.carregar_configuracao():
            print(f"\n✅ Webhook configurado: {self.webhook_id}")

            if self.testar_webhook():
                self.monitorar_automatico()
            else:
                print("\n❌ Não foi possível conectar ao webhook.")
                print("💡 Verifique se está ativo e configurado na W-API!")
        else:
            print("\n❌ Não foi possível configurar o webhook.")


def main():
    """Função principal"""
    monitor = MonitorPortavel()
    monitor.executar()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Monitor encerrado!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

# ========================================
# FORMAS DE USAR EM QUALQUER TERMINAL:
# ========================================
#
# 1. 🚀 EXECUÇÃO SIMPLES:
#    python monitor.py
#    (vai perguntar o webhook na primeira vez)
#
# 2. 📝 COM ARGUMENTO:
#    python monitor.py 0e6e92fd-c357-44e4-b1e5-067d6ae4cd0d
#    python monitor.py https://webhook.site/abc123...
#
# 3. 🔧 VARIÁVEL DE AMBIENTE:
#    export WEBHOOK_ID=0e6e92fd-c357-44e4-b1e5-067d6ae4cd0d
#    python monitor.py
#
# 4. 💾 ARQUIVO SALVO:
#    (configuração é salva automaticamente)
#
# ========================================
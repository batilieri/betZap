#!/usr/bin/env python3
"""
Monitor Rápido de WhatsApp - Funcionamento Imediato
Use este código para monitorar suas mensagens AGORA!
"""

import requests
import json
import time
from datetime import datetime

class MonitorRapido:
    def __init__(self):
        self.mensagens_processadas = set()
        self.contador_mensagens = 0

    def descobrir_webhook_ativo(self):
        """Descobre o webhook que está recebendo suas mensagens"""
        print("🔍 DESCOBRINDO SEU WEBHOOK ATIVO")
        print("=" * 40)
        print("💡 Vou te ajudar a encontrar o webhook que está funcionando!")
        print("\n📋 Como descobrir:")
        print("1. Vá para https://webhook.site")
        print("2. Veja se existe alguma URL que você já criou")
        print("3. Ou crie uma nova URL")
        print("4. Configure essa URL na sua instância W-API")

        print("\n🔗 OPÇÕES:")
        print("1. Tenho o ID do webhook")
        print("2. Quero criar um novo webhook")
        print("3. Não sei como fazer")

        opcao = input("\nEscolha (1-3): ").strip()

        if opcao == '1':
            return self.inserir_webhook_manual()
        elif opcao == '2':
            return self.guia_criar_webhook()
        else:
            return self.guia_completo()

    def inserir_webhook_manual(self):
        """Permite inserir webhook manualmente"""
        print("\n📝 INSERIR WEBHOOK MANUAL")
        print("=" * 30)
        print("💡 Cole o ID do seu webhook (apenas a parte final)")
        print("💡 Exemplo: 12345678-1234-5678-9012-123456789012")

        webhook_input = input("\n🔗 ID do Webhook: ").strip()

        if not webhook_input:
            return None

        # Limpar se foi colada URL completa
        webhook_id = webhook_input.replace('https://webhook.site/', '')
        webhook_id = webhook_id.replace('http://webhook.site/', '')

        # Validar formato básico
        if len(webhook_id) >= 30 and '-' in webhook_id:
            print(f"✅ Webhook ID: {webhook_id}")

            # Testar conectividade
            if self.testar_webhook(webhook_id):
                print("🎉 Webhook está funcionando!")
                return webhook_id
            else:
                print("⚠️ Webhook não responde, mas vamos tentar mesmo assim...")
                return webhook_id
        else:
            print("❌ Formato inválido!")
            return None

    def guia_criar_webhook(self):
        """Guia para criar novo webhook"""
        print("\n🆕 CRIAR NOVO WEBHOOK")
        print("=" * 30)
        print("📋 PASSO A PASSO:")
        print("1. 🌐 Abra https://webhook.site no navegador")
        print("2. 📋 Copie a URL que aparece (ex: https://webhook.site/abc123...)")
        print("3. ⚙️ Configure esta URL na sua instância W-API")
        print("4. 📱 Envie uma mensagem de teste")
        print("5. 🔄 Volte aqui e cole o ID")

        input("\n⏸️ Pressione ENTER quando terminar de configurar...")

        return self.inserir_webhook_manual()

    def guia_completo(self):
        """Guia completo de configuração"""
        print("\n📚 GUIA COMPLETO DE CONFIGURAÇÃO")
        print("=" * 40)
        print("\n🎯 OBJETIVO: Receber mensagens do WhatsApp em tempo real")
        print("\n📋 PASSOS NECESSÁRIOS:")
        print("\n1. 🆕 CRIAR WEBHOOK:")
        print("   • Vá para https://webhook.site")
        print("   • Uma URL será gerada automaticamente")
        print("   • Exemplo: https://webhook.site/12345678-1234-5678-9012-123456789012")

        print("\n2. ⚙️ CONFIGURAR NA W-API:")
        print("   • Acesse o painel da W-API")
        print("   • Vá nas configurações da sua instância")
        print("   • Cole a URL do webhook no campo 'Webhook URL'")
        print("   • Salve as configurações")

        print("\n3. 🧪 TESTAR:")
        print("   • Envie uma mensagem para seu WhatsApp")
        print("   • Verifique se aparece no webhook.site")
        print("   • Se aparecer, está funcionando!")

        print("\n4. 🚀 MONITORAR:")
        print("   • Volte aqui e cole o ID do webhook")
        print("   • O monitor começará a funcionar")

        continuar = input("\n❓ Já configurou tudo? (s/n): ").lower()

        if continuar.startswith('s'):
            return self.inserir_webhook_manual()
        else:
            print("👋 Configure primeiro e volte depois!")
            return None

    def testar_webhook(self, webhook_id):
        """Testa se o webhook está acessível"""
        try:
            url = f"https://webhook.site/token/{webhook_id}/requests"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def monitorar_webhook(self, webhook_id):
        """Monitora o webhook em tempo real"""
        print(f"\n🚀 MONITORANDO WEBHOOK: {webhook_id[:8]}...")
        print("=" * 50)
        print("📱 Mensagens do WhatsApp aparecerão abaixo")
        print("💡 Pressione Ctrl+C para parar")
        print("🔄 Verificando a cada 2 segundos...\n")

        url_api = f"https://webhook.site/token/{webhook_id}/requests"
        inicio = datetime.now()

        try:
            while True:
                try:
                    response = requests.get(url_api, timeout=10)

                    if response.status_code == 200:
                        data = response.json()

                        for request in data.get('data', []):
                            request_id = request.get('uuid')

                            if request_id and request_id not in self.mensagens_processadas:
                                content = request.get('content')

                                if content and isinstance(content, str):
                                    try:
                                        message_data = json.loads(content)

                                        # Verificar se é mensagem do WhatsApp
                                        if message_data.get('event') == 'webhookReceived':
                                            self.contador_mensagens += 1
                                            self.processar_mensagem_whatsapp(message_data)
                                            self.mensagens_processadas.add(request_id)

                                    except json.JSONDecodeError:
                                        # Não é JSON válido, ignorar
                                        pass

                    elif response.status_code == 404:
                        print("❌ Webhook não encontrado ou expirado!")
                        break

                    # Mostrar status a cada 30 segundos
                    tempo_ativo = datetime.now() - inicio
                    if tempo_ativo.seconds % 30 == 0 and tempo_ativo.seconds > 0:
                        print(f"⏱️ Ativo há {tempo_ativo.seconds//60}min | Mensagens: {self.contador_mensagens}")

                    time.sleep(2)

                except requests.RequestException as e:
                    print(f"🔄 Reconectando... (Erro: {str(e)[:30]})")
                    time.sleep(5)
                except Exception as e:
                    print(f"❌ Erro inesperado: {e}")
                    time.sleep(3)

        except KeyboardInterrupt:
            tempo_total = datetime.now() - inicio
            print(f"\n👋 MONITORAMENTO PARADO!")
            print(f"📊 Total de mensagens processadas: {self.contador_mensagens}")
            print(f"⏱️ Tempo total ativo: {tempo_total.seconds//60}min {tempo_total.seconds%60}s")

    def processar_mensagem_whatsapp(self, data):
        """Processa e exibe mensagem do WhatsApp de forma clara"""

        print('\n' + '🟢' * 70)
        print(f'📱 MENSAGEM #{self.contador_mensagens} - {datetime.now().strftime("%H:%M:%S")}')
        print('🟢' * 70)

        # Informações básicas
        instance_id = data.get('instanceId', 'N/A')
        phone = data.get('connectedPhone', 'N/A')
        is_group = data.get('isGroup', False)
        from_me = data.get('fromMe', False)

        print(f"📞 Instância: {instance_id}")
        print(f"📱 Telefone: {phone}")
        print(f"{'👥 GRUPO' if is_group else '👤 PRIVADO'} | {'📤 ENVIADA' if from_me else '📥 RECEBIDA'}")

        # Informações do remetente
        sender = data.get('sender', {})
        sender_name = sender.get('pushName', 'Sem nome')
        sender_id = sender.get('id', 'N/A')

        print(f"\n👤 DE: {sender_name}")
        print(f"📞 ID: {sender_id}")

        # Verificar se é empresa verificada
        if sender.get('verifiedBizName'):
            print(f"🏢 Empresa: {sender.get('verifiedBizName')}")

        # Informações do chat
        chat = data.get('chat', {})
        chat_id = chat.get('id', 'N/A')
        print(f"💭 Chat ID: {chat_id}")

        # Conteúdo da mensagem
        msg_content = data.get('msgContent', {})

        # Verificar tipo de conteúdo
        if 'conversation' in msg_content:
            # Mensagem de texto normal
            texto = msg_content['conversation']
            print(f"\n💬 MENSAGEM:")
            print(f"📝 {texto}")

        elif 'messageStubType' in msg_content:
            # Evento do sistema (alguém entrou/saiu do grupo, etc.)
            stub_type = msg_content['messageStubType']
            parameters = msg_content.get('messageStubParameters', [])

            print(f"\n⚙️ EVENTO DO SISTEMA:")
            print(f"📋 Tipo: {stub_type}")

            # Traduzir eventos comuns
            if stub_type == 'GROUP_PARTICIPANT_ADD':
                print("🎉 Alguém foi adicionado ao grupo")
            elif stub_type == 'GROUP_PARTICIPANT_REMOVE':
                print("👋 Alguém foi removido do grupo")
            elif stub_type == 'GROUP_PARTICIPANT_CHANGE_ROLE':
                print("👑 Cargo de alguém foi alterado no grupo")
            elif stub_type == 'GROUP_CHANGE_SUBJECT':
                print("📝 Nome do grupo foi alterado")
            elif stub_type == 'GROUP_CHANGE_DESCRIPTION':
                print("📄 Descrição do grupo foi alterada")

            if parameters:
                print(f"🔧 Parâmetros: {parameters}")

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
            # Tipo de mensagem desconhecida
            print(f"\n❓ TIPO DE MENSAGEM DESCONHECIDA:")
            print(f"📋 Conteúdo: {json.dumps(msg_content, indent=2)}")

        # Timestamp
        moment = data.get('moment')
        if moment:
            dt = datetime.fromtimestamp(moment)
            print(f"\n🕐 Enviada em: {dt.strftime('%d/%m/%Y às %H:%M:%S')}")

        # ID da mensagem
        message_id = data.get('messageId', 'N/A')
        print(f"🆔 ID: {message_id}")

        print('🟢' * 70 + '\n')

    def executar(self):
        """Executa o monitor"""
        print("🚀 MONITOR RÁPIDO DE WHATSAPP")
        print("=" * 40)
        print("⚡ Este monitor vai funcionar IMEDIATAMENTE!")
        print("📱 Basta ter um webhook configurado")

        webhook_id = self.descobrir_webhook_ativo()

        if webhook_id:
            print(f"\n✅ Webhook configurado: {webhook_id}")
            self.monitorar_webhook(webhook_id)
        else:
            print("\n❌ Não foi possível configurar o webhook.")
            print("💡 Configure um webhook e tente novamente!")

def main():
    """Função principal"""
    monitor = MonitorRapido()
    monitor.executar()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Monitor encerrado!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

# ========================================
# INSTRUÇÕES RÁPIDAS:
# ========================================
#
# 1. 🌐 Vá para https://webhook.site
# 2. 📋 Copie a URL que aparece
# 3. ⚙️ Configure na W-API como webhook
# 4. 🚀 Execute este código
# 5. 📱 Cole o ID do webhook quando pedido
# 6. ✅ Pronto! Mensagens aparecerão aqui
#
# EXEMPLO DE WEBHOOK ID:
# Se a URL for: https://webhook.site/12345678-1234-5678-9012-123456789012
# O ID é: 12345678-1234-5678-9012-123456789012
#
# ========================================
#!/usr/bin/env python3
"""
Leitor de Requisições WhatsApp - Cloudflare Tunnel
Busca e processa as mensagens recebidas pelo webhook
"""

import requests
import json
from datetime import datetime
import time


class WhatsAppRequestsReader:
    """Leitor profissional das requisições do WhatsApp"""

    def __init__(self, tunnel_url):
        self.tunnel_url = tunnel_url.rstrip('/')
        self.requests_endpoint = f"{self.tunnel_url}/requests"
        self.clear_endpoint = f"{self.tunnel_url}/requests/clear"

    def get_all_requests(self):
        """Busca todas as requisições capturadas"""
        try:
            response = requests.get(self.requests_endpoint, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get('requests', [])
            else:
                print(f"❌ Erro: {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Erro ao buscar requisições: {e}")
            return []

    def get_whatsapp_messages(self):
        """Filtra apenas as mensagens do WhatsApp"""
        requests_data = self.get_all_requests()

        whatsapp_messages = []

        for req in requests_data:
            # Verificar se é uma requisição POST com JSON do WhatsApp
            if (req.get('method') == 'POST' and
                    req.get('json') and
                    'event' in req.get('json', {})):
                whatsapp_messages.append(req['json'])

        return whatsapp_messages

    def get_received_messages(self):
        """Filtra apenas mensagens recebidas (não enviadas)"""
        messages = self.get_whatsapp_messages()

        received = []
        for msg in messages:
            if (msg.get('event') == 'webhookReceived' and
                    not msg.get('fromMe', True)):
                received.append(msg)

        return received

    def get_sent_messages(self):
        """Filtra apenas mensagens enviadas"""
        messages = self.get_whatsapp_messages()

        sent = []
        for msg in messages:
            if (msg.get('event') == 'webhookDelivery' and
                    msg.get('fromMe', False)):
                sent.append(msg)

        return sent

    def format_message(self, message):
        """Formata uma mensagem para exibição"""
        try:
            # Informações básicas
            event = message.get('event', '')
            is_from_me = message.get('fromMe', False)
            timestamp = datetime.fromtimestamp(message.get('moment', 0))

            # Informações do remetente
            sender = message.get('sender', {})
            sender_name = sender.get('pushName', 'Sem nome')
            sender_id = sender.get('id', '')

            # Conteúdo da mensagem
            msg_content = message.get('msgContent', {})

            # Texto da conversa
            text = msg_content.get('conversation', '')

            # Se for sticker
            if 'stickerMessage' in msg_content:
                text = '[STICKER]'

            # Direção da mensagem
            direction = "📤 ENVIADA" if is_from_me else "📥 RECEBIDA"

            formatted = f"""
{direction} - {timestamp.strftime('%d/%m/%Y %H:%M:%S')}
👤 De: {sender_name} ({sender_id})
💬 Mensagem: {text}
📱 Event: {event}
"""
            return formatted

        except Exception as e:
            return f"❌ Erro ao formatar mensagem: {e}"

    def show_all_messages(self):
        """Mostra todas as mensagens formatadas"""
        messages = self.get_whatsapp_messages()

        if not messages:
            print("📭 Nenhuma mensagem encontrada")
            return

        print(f"\n📨 TOTAL DE MENSAGENS: {len(messages)}")
        print("=" * 60)

        for i, msg in enumerate(messages, 1):
            print(f"\n📌 MENSAGEM {i}:")
            print(self.format_message(msg))

    def show_received_only(self):
        """Mostra apenas mensagens recebidas"""
        received = self.get_received_messages()

        if not received:
            print("📭 Nenhuma mensagem recebida")
            return

        print(f"\n📥 MENSAGENS RECEBIDAS: {len(received)}")
        print("=" * 60)

        for i, msg in enumerate(received, 1):
            print(f"\n📌 RECEBIDA {i}:")
            print(self.format_message(msg))

    def show_sent_only(self):
        """Mostra apenas mensagens enviadas"""
        sent = self.get_sent_messages()

        if not sent:
            print("📭 Nenhuma mensagem enviada")
            return

        print(f"\n📤 MENSAGENS ENVIADAS: {len(sent)}")
        print("=" * 60)

        for i, msg in enumerate(sent, 1):
            print(f"\n📌 ENVIADA {i}:")
            print(self.format_message(msg))

    def get_statistics(self):
        """Mostra estatísticas das mensagens"""
        all_messages = self.get_whatsapp_messages()
        received = self.get_received_messages()
        sent = self.get_sent_messages()

        print(f"\n📊 ESTATÍSTICAS:")
        print("=" * 30)
        print(f"📨 Total de mensagens: {len(all_messages)}")
        print(f"📥 Mensagens recebidas: {len(received)}")
        print(f"📤 Mensagens enviadas: {len(sent)}")

        # Análise por contato
        contacts = {}
        for msg in all_messages:
            sender_name = msg.get('sender', {}).get('pushName', 'Desconhecido')
            contacts[sender_name] = contacts.get(sender_name, 0) + 1

        print(f"\n👥 MENSAGENS POR CONTATO:")
        for contact, count in contacts.items():
            print(f"   {contact}: {count} mensagens")

    def save_to_file(self, filename="whatsapp_messages.json"):
        """Salva todas as mensagens em arquivo JSON"""
        messages = self.get_whatsapp_messages()


        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)

            print(f"✅ {len(messages)} mensagens salvas em: {filename}")

        except Exception as e:
            print(f"❌ Erro ao salvar arquivo: {e}")

    def clear_requests(self):
        """Limpa todas as requisições do webhook"""
        try:
            response = requests.post(self.clear_endpoint, timeout=10)

            if response.status_code == 200:
                print("✅ Log de requisições limpo com sucesso")
            else:
                print(f"❌ Erro ao limpar: {response.status_code}")

        except Exception as e:
            print(f"❌ Erro: {e}")

    def monitor_new_messages(self, interval=5):
        """Monitora novas mensagens em tempo real"""
        print(f"\n👀 MONITORANDO NOVAS MENSAGENS...")
        print(f"🔄 Verificando a cada {interval} segundos")
        print("💡 Pressione Ctrl+C para parar")
        print("-" * 50)

        last_count = 0

        try:
            while True:
                messages = self.get_whatsapp_messages()
                current_count = len(messages)

                if current_count > last_count:
                    new_messages = messages[last_count:]

                    for msg in new_messages:
                        print(f"\n🆕 NOVA MENSAGEM:")
                        print(self.format_message(msg))

                    last_count = current_count

                time.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n👋 Monitoramento interrompido")


def main():
    """Função principal"""
    # URL do seu túnel (substitua pela sua URL atual)
    tunnel_url = "https://density-survivor-reasonable-twist.trycloudflare.com"

    reader = WhatsAppRequestsReader(tunnel_url)

    while True:
        print("\n📱 WHATSAPP REQUESTS READER")
        print("=" * 40)
        print("1. 📊 Ver estatísticas")
        print("2. 📨 Ver todas as mensagens")
        print("3. 📥 Ver apenas recebidas")
        print("4. 📤 Ver apenas enviadas")
        print("5. 💾 Salvar em arquivo JSON")
        print("6. 👀 Monitorar em tempo real")
        print("7. 🗑️  Limpar requisições")
        print("8. ❌ Sair")

        choice = input("\nEscolha uma opção (1-8): ").strip()

        if choice == "1":
            reader.get_statistics()

        elif choice == "2":
            reader.show_all_messages()

        elif choice == "3":
            reader.show_received_only()

        elif choice == "4":
            reader.show_sent_only()

        elif choice == "5":
            filename = input("Nome do arquivo (padrão: whatsapp_messages.json): ").strip()
            if not filename:
                filename = "whatsapp_messages.json"
            reader.save_to_file(filename)

        elif choice == "6":
            reader.monitor_new_messages()

        elif choice == "7":
            confirm = input("Tem certeza que quer limpar? (s/N): ").lower()
            if confirm == 's':
                reader.clear_requests()

        elif choice == "8":
            print("👋 Saindo...")
            break

        else:
            print("❌ Opção inválida!")


if __name__ == '__main__':
    main()

# =============================================================================
# 🚀 EXEMPLO DE USO RÁPIDO:
# =============================================================================
#
# from whatsapp_reader import WhatsAppRequestsReader
#
# # Criar leitor
# reader = WhatsAppRequestsReader("https://sua-url.trycloudflare.com")
#
# # Buscar todas as mensagens
# messages = reader.get_whatsapp_messages()
# print(f"Total: {len(messages)} mensagens")
#
# # Buscar apenas recebidas
# received = reader.get_received_messages()
# for msg in received:
#     text = msg.get('msgContent', {}).get('conversation', '')
#     sender = msg.get('sender', {}).get('pushName', '')
#     print(f"{sender}: {text}")
#
# =============================================================================
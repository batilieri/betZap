#!/usr/bin/env python3
"""
Monitor WhatsApp com Download Automático de Mídia
Monitora mensagens e processa automaticamente imagens, vídeos, documentos e áudios
"""

import requests
import json
import time
import os
import base64
from datetime import datetime
from pathlib import Path


class MonitorMidiaWhatsApp:
    def __init__(self, webhook_id=None, instance_id=None, bearer_token=None):
        self.webhook_id = webhook_id
        self.instance_id = instance_id
        self.bearer_token = bearer_token
        self.mensagens_processadas = set()
        self.contador_mensagens = 0
        self.contador_midias = 0
        self.base_url = "https://api.w-api.app/v1"

        # Criar pasta para downloads
        self.pasta_downloads = Path("downloads_whatsapp")
        self.pasta_downloads.mkdir(exist_ok=True)

    def carregar_configuracao(self):
        """Carrega configuração de variáveis de ambiente ou solicita"""

        # Tentar variáveis de ambiente primeiro
        self.webhook_id = self.webhook_id or os.getenv('WEBHOOK_ID', '0e6e92fd-c357-44e4-b1e5-067d6ae4cd0d')
        self.instance_id = self.instance_id or os.getenv('WAPI_INSTANCE_ID')
        self.bearer_token = self.bearer_token or os.getenv('WAPI_BEARER_TOKEN')

        # Se não tem configuração da API, solicitar
        if not self.instance_id or not self.bearer_token:
            print("🔧 CONFIGURAÇÃO W-API (para download)")
            print("=" * 40)
            print("💡 Opcional: Para download automático de mídia")
            print("💡 Deixe vazio para apenas monitorar")

            if not self.instance_id:
                self.instance_id = input("📱 Instance ID (opcional): ").strip()

            if not self.bearer_token:
                self.bearer_token = input("🔑 Bearer Token (opcional): ").strip()

        return True

    def eh_mensagem_whatsapp(self, data):
        """Verifica se é uma mensagem válida do WhatsApp"""
        if isinstance(data, dict):
            return any([
                data.get('event') == 'webhookDelivery',
                data.get('event') == 'webhookReceived',
                data.get('event') == 'message',
                'instanceId' in data,
                'msgContent' in data,
                'sender' in data and 'chat' in data
            ])
        return False

    def extrair_informacoes_midia(self, msg_content):
        """Extrai informações de mídia para download"""

        midias_info = []

        # Verificar diferentes tipos de mídia
        tipos_midia = {
            'imageMessage': 'image',
            'videoMessage': 'video',
            'audioMessage': 'audio',
            'documentMessage': 'document',
            'stickerMessage': 'sticker'
        }

        for tipo_msg, tipo_midia in tipos_midia.items():
            if tipo_msg in msg_content:
                midia_data = msg_content[tipo_msg]

                info_midia = {
                    'type': tipo_midia,
                    'mediaKey': midia_data.get('mediaKey'),
                    'directPath': midia_data.get('directPath'),
                    'mimetype': midia_data.get('mimetype'),
                    'url': midia_data.get('url'),
                    'fileLength': midia_data.get('fileLength'),
                    'fileName': midia_data.get('fileName'),
                    'caption': midia_data.get('caption', ''),
                    'fileSha256': midia_data.get('fileSha256'),
                    'fileEncSha256': midia_data.get('fileEncSha256'),
                    'jpegThumbnail': midia_data.get('jpegThumbnail')
                }

                # Adicionar informações específicas do tipo
                if tipo_midia == 'image':
                    info_midia.update({
                        'width': midia_data.get('width'),
                        'height': midia_data.get('height')
                    })
                elif tipo_midia == 'video':
                    info_midia.update({
                        'width': midia_data.get('width'),
                        'height': midia_data.get('height'),
                        'seconds': midia_data.get('seconds')
                    })
                elif tipo_midia == 'audio':
                    info_midia.update({
                        'seconds': midia_data.get('seconds'),
                        'ptt': midia_data.get('ptt', False)  # Push to talk
                    })
                elif tipo_midia == 'document':
                    info_midia.update({
                        'title': midia_data.get('title'),
                        'pageCount': midia_data.get('pageCount')
                    })

                midias_info.append(info_midia)

        return midias_info

    def baixar_midia(self, info_midia, message_id, sender_name):
        """Baixa mídia usando a API W-API"""

        if not self.instance_id or not self.bearer_token:
            print("⚠️ API não configurada - não é possível baixar mídia")
            return None

        if not info_midia.get('mediaKey') or not info_midia.get('directPath'):
            print("❌ Informações de mídia incompletas")
            return None

        url = f"{self.base_url}/media/download"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        params = {
            'instanceId': self.instance_id
        }

        payload = {
            'mediaKey': info_midia['mediaKey'],
            'directPath': info_midia['directPath'],
            'type': info_midia['type'],
            'mimetype': info_midia['mimetype']
        }

        try:
            print(f"📥 Baixando {info_midia['type']}...")
            response = requests.post(url, headers=headers, params=params, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()

                if not result.get('error', True):
                    media_data = result.get('data', {})
                    media_base64 = media_data.get('media')

                    if media_base64:
                        # Decodificar base64
                        media_bytes = base64.b64decode(media_base64)

                        # Gerar nome do arquivo
                        extensao = self.obter_extensao_mimetype(info_midia['mimetype'])
                        nome_arquivo = self.gerar_nome_arquivo(
                            info_midia, message_id, sender_name, extensao
                        )

                        # Salvar arquivo
                        caminho_arquivo = self.pasta_downloads / nome_arquivo
                        with open(caminho_arquivo, 'wb') as f:
                            f.write(media_bytes)

                        print(f"✅ Mídia salva: {caminho_arquivo}")
                        return str(caminho_arquivo)
                    else:
                        print("❌ Dados de mídia não encontrados na resposta")
                        return None
                else:
                    print(f"❌ Erro na API: {result.get('message', 'Erro desconhecido')}")
                    return None
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Erro ao baixar mídia: {e}")
            return None

    def obter_extensao_mimetype(self, mimetype):
        """Obtém extensão baseada no mimetype"""

        mimetypes_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'video/mp4': '.mp4',
            'video/avi': '.avi',
            'video/mov': '.mov',
            'audio/mpeg': '.mp3',
            'audio/ogg': '.ogg',
            'audio/wav': '.wav',
            'audio/mp4': '.m4a',
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'text/plain': '.txt'
        }

        return mimetypes_map.get(mimetype, '.bin')

    def gerar_nome_arquivo(self, info_midia, message_id, sender_name, extensao):
        """Gera nome único para o arquivo"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Limpar nome do remetente
        sender_clean = "".join(c for c in sender_name if c.isalnum() or c in (' ', '-', '_')).strip()
        sender_clean = sender_clean.replace(' ', '_')

        # Se tem nome de arquivo original, usar
        if info_midia.get('fileName'):
            nome_original = info_midia['fileName']
            nome_sem_ext = os.path.splitext(nome_original)[0]
            return f"{timestamp}_{sender_clean}_{nome_sem_ext}{extensao}"

        # Senão, usar tipo e ID da mensagem
        tipo = info_midia['type']
        message_short = message_id[:8] if message_id else "unknown"

        return f"{timestamp}_{sender_clean}_{tipo}_{message_short}{extensao}"

    def processar_mensagem_whatsapp(self, data):
        """Processa mensagem e extrai/baixa mídias"""

        self.contador_mensagens += 1

        print('\n' + '🟢' * 70)
        print(f'📱 MENSAGEM #{self.contador_mensagens} - {datetime.now().strftime("%H:%M:%S")}')
        print('🟢' * 70)

        # Informações básicas
        instance_id = data.get('instanceId', 'N/A')
        phone = data.get('connectedPhone', 'N/A')
        is_group = data.get('isGroup', False)
        from_me = data.get('fromMe', False)
        message_id = data.get('messageId', 'N/A')

        print(f"📞 Instância: {instance_id}")
        print(f"📱 Telefone: {phone}")
        print(f"🆔 Message ID: {message_id}")
        print(f"{'👥 GRUPO' if is_group else '👤 PRIVADO'} | {'📤 ENVIADA' if from_me else '📥 RECEBIDA'}")

        # Informações do remetente
        sender = data.get('sender', {})
        sender_name = sender.get('pushName', 'Sem nome')
        sender_id = sender.get('id', 'N/A')

        print(f"\n👤 DE: {sender_name}")
        print(f"📞 ID: {sender_id}")

        # Informações do chat
        chat = data.get('chat', {})
        chat_id = chat.get('id', 'N/A')
        print(f"💭 Chat ID: {chat_id}")

        # Processar conteúdo da mensagem
        msg_content = data.get('msgContent', {})

        if msg_content:
            # Verificar se há texto
            if 'conversation' in msg_content:
                print(f"\n💬 MENSAGEM:")
                print(f"📝 {msg_content['conversation']}")

            # Extrair informações de mídia
            midias_info = self.extrair_informacoes_midia(msg_content)

            if midias_info:
                print(f"\n📎 MÍDIA DETECTADA ({len(midias_info)} arquivo(s)):")

                for i, info_midia in enumerate(midias_info, 1):
                    self.contador_midias += 1

                    print(f"\n📄 Arquivo #{i}:")
                    print(f"   🎯 Tipo: {info_midia['type']}")
                    print(f"   📋 Mimetype: {info_midia['mimetype']}")

                    if info_midia.get('fileName'):
                        print(f"   📁 Nome: {info_midia['fileName']}")

                    if info_midia.get('fileLength'):
                        size_mb = int(info_midia['fileLength']) / (1024 * 1024)
                        print(f"   📏 Tamanho: {size_mb:.2f} MB")

                    if info_midia.get('caption'):
                        print(f"   📝 Legenda: {info_midia['caption']}")

                    # Informações específicas do tipo
                    if info_midia['type'] in ['image', 'video']:
                        width = info_midia.get('width')
                        height = info_midia.get('height')
                        if width and height:
                            print(f"   📐 Dimensões: {width}x{height}")

                    if info_midia['type'] in ['video', 'audio']:
                        seconds = info_midia.get('seconds')
                        if seconds:
                            print(f"   ⏱️ Duração: {seconds}s")

                    # Exibir informações para download manual
                    print(f"\n   🔧 DADOS PARA DOWNLOAD:")
                    print(f"   mediaKey: {info_midia.get('mediaKey', 'N/A')}")
                    print(f"   directPath: {info_midia.get('directPath', 'N/A')}")
                    print(f"   type: {info_midia['type']}")
                    print(f"   mimetype: {info_midia['mimetype']}")

                    # Tentar baixar automaticamente
                    if self.instance_id and self.bearer_token:
                        caminho_arquivo = self.baixar_midia(info_midia, message_id, sender_name)
                        if caminho_arquivo:
                            print(f"   ✅ Baixado: {caminho_arquivo}")
                    else:
                        print(f"   💡 Configure API para download automático")

        # Timestamp
        moment = data.get('moment')
        if moment:
            dt = datetime.fromtimestamp(moment)
            print(f"\n🕐 Enviada em: {dt.strftime('%d/%m/%Y às %H:%M:%S')}")

        print('🟢' * 70 + '\n')

    def buscar_mensagens_novas(self):
        """Busca mensagens novas no webhook"""
        try:
            url = f"https://webhook.site/token/{self.webhook_id}/requests"
            response = requests.get(url, timeout=10)

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

                                if self.eh_mensagem_whatsapp(message_data):
                                    mensagens_novas.append({
                                        'id': request_id,
                                        'data': message_data
                                    })
                                    self.mensagens_processadas.add(request_id)

                            except json.JSONDecodeError:
                                pass

                return mensagens_novas

            elif response.status_code == 404:
                print("❌ Webhook não encontrado ou expirado!")
                return None
            else:
                return []

        except Exception as e:
            print(f"⚠️ Erro ao buscar mensagens: {e}")
            return []

    def monitorar_com_midia(self):
        """Monitora mensagens e processa mídias"""

        print(f"\n🚀 MONITOR COM PROCESSAMENTO DE MÍDIA")
        print("=" * 50)
        print(f"🔗 Webhook: {self.webhook_id}")
        print(f"📁 Downloads: {self.pasta_downloads}")

        if self.instance_id and self.bearer_token:
            print(f"📱 Instance: {self.instance_id}")
            print("✅ Download automático ATIVO")
        else:
            print("⚠️ Download manual (dados serão exibidos)")

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
                    print(
                        f"⏱️ Ativo há {tempo_ativo.seconds // 60}min | Mensagens: {self.contador_mensagens} | Mídias: {self.contador_midias}")

                time.sleep(3)

        except KeyboardInterrupt:
            tempo_total = datetime.now() - inicio
            print(f"\n👋 MONITORAMENTO PARADO!")
            print(f"📊 Mensagens processadas: {self.contador_mensagens}")
            print(f"📎 Mídias encontradas: {self.contador_midias}")
            print(f"⏱️ Tempo ativo: {tempo_total.seconds // 60}min {tempo_total.seconds % 60}s")
            print(f"📁 Downloads salvos em: {self.pasta_downloads}")

    def executar(self):
        """Executa o monitor"""

        print("📎 MONITOR WHATSAPP COM MÍDIA")
        print("=" * 40)
        print("🎯 Detecta e processa imagens, vídeos, áudios e documentos")

        if self.carregar_configuracao():
            print(f"\n✅ Webhook: {self.webhook_id}")

            if self.instance_id and self.bearer_token:
                print("🔧 API configurada - download automático ATIVO")
            else:
                print("💡 API não configurada - apenas exibição de dados")

            self.monitorar_com_midia()


def main():
    """Função principal"""
    monitor = MonitorMidiaWhatsApp()
    monitor.executar()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Monitor encerrado!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

# ========================================
# CONFIGURAÇÃO VIA VARIÁVEIS DE AMBIENTE:
# ========================================
#
# export WEBHOOK_ID=seu_webhook_id
# export WAPI_INSTANCE_ID=sua_instancia  
# export WAPI_BEARER_TOKEN=seu_token
# python monitor_midia.py
#
# ========================================
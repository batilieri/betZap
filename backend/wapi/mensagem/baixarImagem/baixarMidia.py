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
    def __init__(self, webhook_id, instance_id, bearer_token):
        self.webhook_id = webhook_id
        self.instance_id = instance_id
        self.bearer_token = bearer_token
        self.mensagens_processadas = set()
        self.contador_mensagens = 0
        self.contador_midias = 0
        self.base_url = "https://api.w-api.app/v1"

        # Criar pastas organizadas para downloads
        self.pasta_downloads = Path("downloads_whatsapp")
        self.pasta_downloads.mkdir(exist_ok=True)

        # Criar subpastas por tipo de mídia
        self.pastas_midia = {
            'image': self.pasta_downloads / "imagens",
            'video': self.pasta_downloads / "videos",
            'audio': self.pasta_downloads / "audios",
            'document': self.pasta_downloads / "documentos",
            'sticker': self.pasta_downloads / "stickers"
        }

        for pasta in self.pastas_midia.values():
            pasta.mkdir(exist_ok=True)

    def carregar_configuracao(self):
        """Valida se os parâmetros necessários foram fornecidos"""
        if not self.instance_id or not self.bearer_token:
            print("🔧 CONFIGURAÇÃO W-API (para download)")
            print("=" * 40)
            print("⚠️ Instance ID e Bearer Token são obrigatórios para download automático")
            return False
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
        """Extrai informações de mídia para download com validação"""
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

                # Verificar campos obrigatórios de criptografia
                campos_obrigatorios = ['mediaKey', 'directPath', 'fileEncSha256', 'fileSha256']
                if not all(midia_data.get(campo) for campo in campos_obrigatorios):
                    print(f"⚠️ {tipo_midia} sem dados de criptografia completos - download não disponível")
                    continue

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
                    'jpegThumbnail': midia_data.get('jpegThumbnail'),
                    'mediaKeyTimestamp': midia_data.get('mediaKeyTimestamp')
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
                        'ptt': midia_data.get('ptt', False),
                        'waveform': midia_data.get('waveform')
                    })
                elif tipo_midia == 'document':
                    info_midia.update({
                        'title': midia_data.get('title'),
                        'pageCount': midia_data.get('pageCount')
                    })
                elif tipo_midia == 'sticker':
                    info_midia.update({
                        'isAnimated': midia_data.get('isAnimated', False),
                        'isAvatar': midia_data.get('isAvatar', False),
                        'isAiSticker': midia_data.get('isAiSticker', False),
                        'isLottie': midia_data.get('isLottie', False)
                    })

                midias_info.append(info_midia)

        return midias_info


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
            'video/3gpp': '.3gp',
            'audio/mpeg': '.mp3',
            'audio/ogg': '.ogg',
            'audio/wav': '.wav',
            'audio/mp4': '.m4a',
            'audio/ogg; codecs=opus': '.ogg',
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
        sender_clean = sender_clean.replace(' ', '_')[:20]  # Limitar tamanho

        # Se tem nome de arquivo original, usar
        if info_midia.get('fileName'):
            nome_original = info_midia['fileName']
            nome_sem_ext = os.path.splitext(nome_original)[0][:30]  # Limitar tamanho
            return f"{timestamp}_{sender_clean}_{nome_sem_ext}{extensao}"

        # Senão, usar tipo e ID da mensagem
        tipo = info_midia['type']
        message_short = message_id[:8] if message_id else "unknown"

        return f"{timestamp}_{sender_clean}_{tipo}_{message_short}{extensao}"

    def processar_mensagem_whatsapp(self, data):
        """Processa mensagem e extrai/baixa mídias - versão corrigida"""
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
                    print(f"   📁 Pasta: {self.pastas_midia[info_midia['type']]}")

                    if info_midia.get('fileName'):
                        print(f"   📄 Nome: {info_midia['fileName']}")

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

                    # Tentar baixar automaticamente
                    if self.instance_id and self.bearer_token:
                        # Tentar método principal primeiro
                        caminho_arquivo = self.baixar_midia(info_midia, message_id, sender_name)

                        # Se falhar, tentar método alternativo
                        if not caminho_arquivo and info_midia.get('url'):
                            print("   🔄 Tentando método alternativo...")
                            caminho_arquivo = self.baixar_midia_alternativo(info_midia, message_id, sender_name)

                        if caminho_arquivo:
                            print(f"   ✅ Baixado: {caminho_arquivo}")
                        else:
                            print(f"   ❌ Falha no download")
                            # Salvar dados para tentativa manual posterior
                            self.salvar_dados_para_download_manual(info_midia, message_id, sender_name)
                    else:
                        print(f"   💡 Configure API para download automático")
                        self.salvar_dados_para_download_manual(info_midia, message_id, sender_name)

        # Timestamp
        moment = data.get('moment')
        if moment:
            dt = datetime.fromtimestamp(moment)
            print(f"\n🕐 Enviada em: {dt.strftime('%d/%m/%Y às %H:%M:%S')}")

        print('🟢' * 70 + '\n')

    def salvar_dados_para_download_manual(self, info_midia, message_id, sender_name):
        """Salva dados para download manual posterior"""
        arquivo_pendentes = self.pasta_downloads / "downloads_pendentes.json"

        dados_download = {
            'message_id': message_id,
            'sender_name': sender_name,
            'timestamp': datetime.now().isoformat(),
            'media_info': info_midia
        }

        try:
            if arquivo_pendentes.exists():
                with open(arquivo_pendentes, 'r', encoding='utf-8') as f:
                    pendentes = json.load(f)
            else:
                pendentes = []

            pendentes.append(dados_download)

            with open(arquivo_pendentes, 'w', encoding='utf-8') as f:
                json.dump(pendentes, f, indent=2, ensure_ascii=False)

            print(f"   💾 Dados salvos para download manual")

        except Exception as e:
            print(f"   ⚠️ Erro ao salvar dados: {e}")

    def baixar_midia(self, info_midia, message_id, sender_name):
        """Baixa mídia usando a API W-API com validação de criptografia"""
        if not self.instance_id or not self.bearer_token:
            print("⚠️ API não configurada - não é possível baixar mídia")
            return None

        # Validar dados de criptografia obrigatórios
        campos_necessarios = ['mediaKey', 'directPath', 'fileEncSha256', 'fileSha256']
        for campo in campos_necessarios:
            if not info_midia.get(campo):
                print(f"❌ {campo} ausente - necessário para download")
                return None

        # URL corrigida baseada na documentação
        url = f"{self.base_url}/message/download-media"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        params = {
            'instanceId': self.instance_id
        }

        # Payload corrigido conforme documentação da API
        payload = {
            'mediaKey': info_midia['mediaKey'],
            'directPath': info_midia['directPath'],
            'type': info_midia['type'],
            'mimetype': info_midia['mimetype']
        }

        try:
            print(f"📥 Baixando {info_midia['type']} com validação criptográfica...")
            print(f"   🔧 URL: {url}")
            print(f"   🔧 Payload: {json.dumps(payload, indent=2)}")

            response = requests.post(url, headers=headers, params=params, json=payload, timeout=30)

            print(f"   📊 Status: {response.status_code}")
            print(f"   📝 Response: {response.text[:200]}...")

            if response.status_code == 200:
                result = response.json()

                # Verificar se a resposta tem dados de mídia
                if 'data' in result and result['data']:
                    media_data = result['data']

                    # Diferentes formatos de resposta da API
                    media_base64 = None
                    if isinstance(media_data, str):
                        media_base64 = media_data
                    elif isinstance(media_data, dict):
                        media_base64 = media_data.get('media') or media_data.get('buffer') or media_data.get('data')

                    if media_base64:
                        # Decodificar base64
                        try:
                            media_bytes = base64.b64decode(media_base64)
                        except Exception as e:
                            print(f"❌ Erro ao decodificar base64: {e}")
                            return None

                        # Gerar nome do arquivo e metadados
                        extensao = self.obter_extensao_mimetype(info_midia['mimetype'])
                        nome_arquivo = self.gerar_nome_arquivo(
                            info_midia, message_id, sender_name, extensao
                        )

                        # Salvar na pasta específica do tipo
                        pasta_tipo = self.pastas_midia[info_midia['type']]
                        caminho_arquivo = pasta_tipo / nome_arquivo

                        with open(caminho_arquivo, 'wb') as f:
                            f.write(media_bytes)

                        # Salvar metadados do arquivo para referência futura
                        self.salvar_metadados_arquivo(caminho_arquivo, info_midia, message_id, sender_name)

                        print(f"✅ {info_midia['type'].title()} salvo: {caminho_arquivo}")
                        return str(caminho_arquivo)
                    else:
                        print("❌ Dados de mídia não encontrados na resposta")
                        return None
                else:
                    print(f"❌ Erro na API: {result.get('message', 'Resposta sem dados')}")
                    return None
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                print(f"   📄 Resposta completa: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Erro ao baixar mídia: {e}")
            return None

    def salvar_metadados_arquivo(self, caminho_arquivo, info_midia, message_id, sender_name):
        """Salva metadados do arquivo para facilitar localização futura"""
        metadados = {
            'message_id': message_id,
            'sender_name': sender_name,
            'type': info_midia['type'],
            'mimetype': info_midia['mimetype'],
            'file_path': str(caminho_arquivo),
            'file_name': caminho_arquivo.name,
            'download_timestamp': datetime.now().isoformat(),
            'original_data': {
                'mediaKey': info_midia.get('mediaKey'),
                'directPath': info_midia.get('directPath'),
                'fileLength': info_midia.get('fileLength'),
                'fileName': info_midia.get('fileName'),
                'caption': info_midia.get('caption'),
                'width': info_midia.get('width'),
                'height': info_midia.get('height'),
                'seconds': info_midia.get('seconds'),
                'ptt': info_midia.get('ptt'),
                'mediaKeyTimestamp': info_midia.get('mediaKeyTimestamp')
            }
        }

        # Salvar arquivo de metadados JSON
        arquivo_metadados = caminho_arquivo.with_suffix('.meta.json')
        with open(arquivo_metadados, 'w', encoding='utf-8') as f:
            json.dump(metadados, f, indent=2, ensure_ascii=False)

        # Atualizar índice geral de mídias
        self.atualizar_indice_midias(metadados)

    def atualizar_indice_midias(self, metadados):
        """Atualiza índice geral de todas as mídias baixadas"""
        arquivo_indice = self.pasta_downloads / "indice_midias.json"

        try:
            if arquivo_indice.exists():
                with open(arquivo_indice, 'r', encoding='utf-8') as f:
                    indice = json.load(f)
            else:
                indice = {
                    'total_arquivos': 0,
                    'ultima_atualizacao': None,
                    'arquivos': [],
                    'estatisticas': {
                        'image': 0,
                        'video': 0,
                        'audio': 0,
                        'document': 0,
                        'sticker': 0
                    }
                }

            # Adicionar novo arquivo
            indice['arquivos'].append(metadados)
            indice['total_arquivos'] = len(indice['arquivos'])
            indice['ultima_atualizacao'] = datetime.now().isoformat()
            indice['estatisticas'][metadados['type']] += 1

            # Salvar índice atualizado
            with open(arquivo_indice, 'w', encoding='utf-8') as f:
                json.dump(indice, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"⚠️ Erro ao atualizar índice: {e}")

    def buscar_midia_por_message_id(self, message_id):
        """Busca arquivo de mídia pelo ID da mensagem"""
        arquivo_indice = self.pasta_downloads / "indice_midias.json"

        if not arquivo_indice.exists():
            return None

        try:
            with open(arquivo_indice, 'r', encoding='utf-8') as f:
                indice = json.load(f)

            for arquivo in indice['arquivos']:
                if arquivo['message_id'] == message_id:
                    return arquivo

            return None
        except Exception as e:
            print(f"❌ Erro ao buscar mídia: {e}")
            return None

    def buscar_mensagens_novas(self):
        """Busca mensagens novas no webhook"""
        try:
            url = self.webhook_id
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                requests_data = data.get('requests', [])

                mensagens_novas = []

                for request in requests_data:
                    # Usar timestamp como ID único
                    request_id = request.get('timestamp', '')

                    if request_id and request_id not in self.mensagens_processadas:
                        # Os dados já vêm no campo 'json' ou 'data'
                        message_data = request.get('json') or request.get('data')

                        if message_data and self.eh_mensagem_whatsapp(message_data):
                            mensagens_novas.append({
                                'id': request_id,
                                'data': message_data
                            })
                            self.mensagens_processadas.add(request_id)

                return mensagens_novas

            elif response.status_code == 404:
                print("❌ Webhook não encontrado ou expirado!")
                return None
            else:
                return []

        except Exception as e:
            print(f"⚠️ Erro ao buscar mensagens: {e}")
            return []

    def listar_midias_por_tipo(self, tipo_midia):
        """Lista todas as mídias de um tipo específico"""
        arquivo_indice = self.pasta_downloads / "indice_midias.json"

        if not arquivo_indice.exists():
            return []

        try:
            with open(arquivo_indice, 'r', encoding='utf-8') as f:
                indice = json.load(f)

            return [arquivo for arquivo in indice['arquivos'] if arquivo['type'] == tipo_midia]
        except Exception as e:
            print(f"❌ Erro ao listar mídias: {e}")
            return []

    def obter_estatisticas_downloads(self):
        """Retorna estatísticas dos downloads"""
        arquivo_indice = self.pasta_downloads / "indice_midias.json"

        if not arquivo_indice.exists():
            return {
                'total': 0,
                'por_tipo': {},
                'ultima_atualizacao': None
            }

        try:
            with open(arquivo_indice, 'r', encoding='utf-8') as f:
                indice = json.load(f)

            return {
                'total': indice['total_arquivos'],
                'por_tipo': indice['estatisticas'],
                'ultima_atualizacao': indice['ultima_atualizacao']
            }
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return {'total': 0, 'por_tipo': {}, 'ultima_atualizacao': None}

    def baixar_midia_alternativo(self, info_midia, message_id, sender_name):
        """Método alternativo usando URL direta quando disponível"""
        if not info_midia.get('url'):
            print("❌ URL direta não disponível")
            return None

        try:
            print(f"📥 Tentando download direto da URL...")
            response = requests.get(info_midia['url'], timeout=30)

            if response.status_code == 200:
                # Gerar nome do arquivo
                extensao = self.obter_extensao_mimetype(info_midia['mimetype'])
                nome_arquivo = self.gerar_nome_arquivo(
                    info_midia, message_id, sender_name, extensao
                )

                # Salvar arquivo
                pasta_tipo = self.pastas_midia[info_midia['type']]
                caminho_arquivo = pasta_tipo / nome_arquivo

                with open(caminho_arquivo, 'wb') as f:
                    f.write(response.content)

                # Salvar metadados
                self.salvar_metadados_arquivo(caminho_arquivo, info_midia, message_id, sender_name)

                print(f"✅ Download direto bem-sucedido: {caminho_arquivo}")
                return str(caminho_arquivo)
            else:
                print(f"❌ Erro no download direto: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Erro no download alternativo: {e}")
            return None

    def monitorar_com_midia(self):
        """Monitora mensagens e processa mídias"""
        print(f"\n🚀 MONITOR COM PROCESSAMENTO DE MÍDIA")
        print("=" * 50)
        print(f"🔗 Webhook: {self.webhook_id}")
        print(f"📁 Downloads: {self.pasta_downloads}")
        print(f"📂 Pastas organizadas:")
        for tipo, pasta in self.pastas_midia.items():
            print(f"   {tipo}: {pasta}")

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
            print("🔧 API configurada - download automático ATIVO")
            self.monitorar_com_midia()
        else:
            print("❌ Configuração incompleta. Forneça instance_id e bearer_token.")


if __name__ == '__main__':
    try:
        instance_id = "3B6XIW-ZTS923-GEAY6V"
        bearer_token = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"
        web_hooks = "https://dream-photographs-tom-demographic.trycloudflare.com/requests?limit=100"
        monitor = MonitorMidiaWhatsApp(
            webhook_id=web_hooks,
            instance_id=instance_id,
            bearer_token=bearer_token
        )
        monitor.executar()
    except KeyboardInterrupt:
        print("\n👋 Monitor encerrado!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
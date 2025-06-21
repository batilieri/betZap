#!/usr/bin/env python3
"""
Monitor WhatsApp com Download e Descriptografia Automática de Mídia
Monitora mensagens, descriptografa e organiza automaticamente imagens, vídeos, documentos e áudios
"""

import requests
import json
import time
import os
import base64
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from backend.banco.database_manager_updated import WhatsAppDatabaseManager
from backend.banco.models_updated import WebhookEvent


class BaixarMidias:
    def __init__(self, webhook_id: str, instance_id: str, bearer_token: str, db_path: str = None):
        self.webhook_id = webhook_id
        self.instance_id = instance_id
        self.bearer_token = bearer_token
        self.mensagens_processadas = set()
        self.contador_mensagens = 0
        self.contador_midias = 0
        self.base_url = "https://api.w-api.app/v1"

        # Configurar banco de dados
        if db_path:
            self.db_path = db_path
        else:
            # Partir do diretório do script atual
            script_dir = Path(__file__).parent  # .../baixarmidias/
            backend_dir = script_dir.parent.parent.parent  # Voltar para .../backend/
            self.db_path = str(backend_dir / "banco" / "whatsapp_webhook_realtime.db")

        self._init_database()
        phafNow = Path(__file__).parent  # .../baixarmidias/
        phafMidias = phafNow.parent.parent.parent.parent  # Voltar para .../backend/
        self.pasta_downloads = Path(phafMidias / "midias")
        self.pasta_downloads.mkdir(exist_ok=True)

        self.pastas_midia = {
            'image': self.pasta_downloads / "imagens",
            'video': self.pasta_downloads / "videos",
            'audio': self.pasta_downloads / "audios",
            'document': self.pasta_downloads / "documentos",
            'sticker': self.pasta_downloads / "stickers"
        }

        for pasta in self.pastas_midia.values():
            pasta.mkdir(exist_ok=True)

    def _init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        try:
            # Garantir que o diretório existe
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Tabela principal de mídias
                cursor.execute('''
                   CREATE TABLE IF NOT EXISTS whatsapp_midias (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       message_id TEXT UNIQUE NOT NULL,
                       sender_name TEXT NOT NULL,
                       sender_id TEXT NOT NULL,
                       chat_id TEXT NOT NULL,
                       is_group BOOLEAN NOT NULL,
                       from_me BOOLEAN NOT NULL,
                       media_type TEXT NOT NULL,
                       mimetype TEXT NOT NULL,
                       file_name TEXT,
                       file_path TEXT,
                       file_size INTEGER,
                       caption TEXT,
                       width INTEGER,
                       height INTEGER,
                       duration_seconds INTEGER,
                       is_ptt BOOLEAN,
                       download_status TEXT DEFAULT 'pending',
                       download_timestamp DATETIME,
                       message_timestamp DATETIME,
                       media_key TEXT,
                       direct_path TEXT,
                       file_sha256 TEXT,
                       file_enc_sha256 TEXT,
                       media_key_timestamp TEXT,
                       created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                       updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                   )
               ''')

                # Índices para otimizar consultas
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_id ON whatsapp_midias(message_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_type ON whatsapp_midias(media_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_status ON whatsapp_midias(download_status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sender_id ON whatsapp_midias(sender_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_id ON whatsapp_midias(chat_id)')

                conn.commit()
                print("✅ Banco de dados inicializado")

        except Exception as e:
            print(f"❌ Erro ao inicializar banco: {e}")

    def salvar_midia_no_banco(self, message_data: Dict, info_midia: Dict, file_path: str = None) -> bool:
        """Salva informações da mídia no banco de dados - COM INTEGRAÇÃO"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Extrair informações da mensagem
                message_id = message_data.get('messageId', '')
                sender = message_data.get('sender', {})
                chat = message_data.get('chat', {})
                moment = message_data.get('moment')

                message_timestamp = None
                if moment:
                    message_timestamp = datetime.fromtimestamp(moment)

                # Preparar dados para inserção na tabela whatsapp_midias
                dados = (
                    message_id,
                    sender.get('pushName', 'Sem nome'),
                    sender.get('id', ''),
                    chat.get('id', ''),
                    message_data.get('isGroup', False),
                    message_data.get('fromMe', False),
                    info_midia['type'],
                    info_midia['mimetype'],
                    info_midia.get('fileName'),
                    file_path,
                    info_midia.get('fileLength'),
                    info_midia.get('caption', ''),
                    info_midia.get('width'),
                    info_midia.get('height'),
                    info_midia.get('seconds'),
                    info_midia.get('ptt', False),
                    'success' if file_path else 'pending',
                    datetime.now() if file_path else None,
                    message_timestamp,
                    info_midia.get('mediaKey'),
                    info_midia.get('directPath'),
                    info_midia.get('fileSha256'),
                    info_midia.get('fileEncSha256'),
                    info_midia.get('mediaKeyTimestamp')
                )

                cursor.execute('''
                    INSERT OR REPLACE INTO whatsapp_midias (
                        message_id, sender_name, sender_id, chat_id, is_group, from_me,
                        media_type, mimetype, file_name, file_path, file_size, caption,
                        width, height, duration_seconds, is_ptt, download_status,
                        download_timestamp, message_timestamp, media_key, direct_path,
                        file_sha256, file_enc_sha256, media_key_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', dados)

                conn.commit()

                # NOVO: Se temos file_path, atualizar vínculo na tabela de relacionamento
                if file_path:
                    # Buscar event_id correspondente
                    cursor.execute('''
                        SELECT id FROM webhook_events WHERE message_id = ?
                    ''', (message_id,))

                    row = cursor.fetchone()
                    if row:
                        event_id = row[0]

                        # Atualizar MessageMedia
                        cursor.execute('''
                            UPDATE whatsapp_message_medias 
                            SET media_path = ?, download_status = 'success'
                            WHERE event_id = ? AND media_type = ? AND download_status = 'pending'
                        ''', (file_path, event_id, info_midia['type']))

                        conn.commit()

                return True

        except Exception as e:
            print(f"❌ Erro ao salvar mídia integrada: {e}")
            return False

    def buscar_midias_pendentes(self) -> List[Dict]:
        """Busca mídias com download pendente no banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                   SELECT * FROM whatsapp_midias 
                   WHERE download_status = 'pending' OR download_status = 'failed'
                   ORDER BY created_at DESC
               ''')

                colunas = [desc[0] for desc in cursor.description]
                resultados = cursor.fetchall()

                return [dict(zip(colunas, row)) for row in resultados]

        except Exception as e:
            print(f"❌ Erro ao buscar mídias pendentes: {e}")
            return []

    def atualizar_status_download(self, message_id: str, status: str, file_path: str = None):
        """Atualiza status do download no banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if file_path:
                    cursor.execute('''
                       UPDATE whatsapp_midias 
                       SET download_status = ?, file_path = ?, download_timestamp = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE message_id = ?
                   ''', (status, file_path, datetime.now(), message_id))
                else:
                    cursor.execute('''
                       UPDATE whatsapp_midias 
                       SET download_status = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE message_id = ?
                   ''', (status, message_id))

                conn.commit()

        except Exception as e:
            print(f"❌ Erro ao atualizar status: {e}")

    def eh_mensagem_whatsapp(self, data: Dict) -> bool:
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

    def extrair_informacoes_midia(self, msg_content: Dict) -> List[Dict]:
        """Extrai informações de mídia para download"""
        midias_info = []

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

                # Verificar campos obrigatórios
                campos_obrigatorios = ['mediaKey', 'directPath', 'fileEncSha256', 'fileSha256']
                if not all(midia_data.get(campo) for campo in campos_obrigatorios):
                    print(f"⚠️ {tipo_midia} sem dados completos para descriptografia")
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

                # Adicionar dados específicos por tipo
                if tipo_midia in ['image', 'video']:
                    info_midia.update({
                        'width': midia_data.get('width'),
                        'height': midia_data.get('height')
                    })

                if tipo_midia in ['video', 'audio']:
                    info_midia['seconds'] = midia_data.get('seconds')

                if tipo_midia == 'audio':
                    info_midia.update({
                        'ptt': midia_data.get('ptt', False),
                        'waveform': midia_data.get('waveform')
                    })

                if tipo_midia == 'document':
                    info_midia.update({
                        'title': midia_data.get('title'),
                        'pageCount': midia_data.get('pageCount')
                    })

                if tipo_midia == 'sticker':
                    info_midia.update({
                        'isAnimated': midia_data.get('isAnimated', False),
                        'isAvatar': midia_data.get('isAvatar', False)
                    })

                midias_info.append(info_midia)

        return midias_info

    def obter_extensao_mimetype(self, mimetype: str) -> str:
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

    def descriptografar_e_baixar_midia(self, info_midia: Dict, message_id: str, sender_name: str) -> Optional[str]:
        """Descriptografa e baixa mídia usando a API com validação completa - CORRIGIDO"""
        if not self.instance_id or not self.bearer_token:
            print("⚠️ API não configurada")
            return None

        # Validar campos obrigatórios para descriptografia
        campos_necessarios = ['mediaKey', 'directPath', 'fileEncSha256', 'fileSha256']
        for campo in campos_necessarios:
            if not info_midia.get(campo):
                print(f"❌ {campo} ausente - necessário para descriptografia")
                return None

        # URL da API de download
        url = f"{self.base_url}/message/download-media"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        params = {'instanceId': self.instance_id}

        # Payload CORRIGIDO - remover campos extras que causam problemas
        payload = {
            'mediaKey': info_midia['mediaKey'],
            'directPath': info_midia['directPath'],
            'type': info_midia['type'],
            'mimetype': info_midia['mimetype']
        }

        try:
            print(f"🔓 Descriptografando {info_midia['type']}...")

            response = requests.post(url, headers=headers, params=params, json=payload, timeout=60)
            print(f"   📊 Status: {response.status_code}")

            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()

                if 'application/json' in content_type:
                    # Resposta JSON com dados base64
                    result = response.json()

                    # CORREÇÃO: Verificar se há erro na resposta da API
                    if 'error' in result:
                        error_msg = result.get('error', 'Erro desconhecido')
                        print(f"❌ Erro da API: {error_msg}")

                        # Se há fileLink, tentar download direto
                        if 'fileLink' in result and result['fileLink']:
                            print(f"   🔄 Tentando download direto via fileLink...")
                            return self._baixar_via_filelink(result['fileLink'], info_midia, message_id, sender_name)

                        return None

                    # Verificar estrutura da resposta mais robustamente
                    media_data = None
                    if 'data' in result:
                        media_data = result['data']
                    elif 'media' in result:
                        media_data = result['media']
                    elif 'buffer' in result:
                        media_data = result['buffer']
                    elif 'file' in result:
                        media_data = result['file']
                    elif 'fileLink' in result and result['fileLink']:
                        # API retornou link direto em vez de dados base64
                        print(f"   🔄 API retornou fileLink, fazendo download direto...")
                        return self._baixar_via_filelink(result['fileLink'], info_midia, message_id, sender_name)

                    if not media_data:
                        print(f"❌ Dados de mídia não encontrados na resposta")
                        print(f"   📄 Estrutura resposta: {list(result.keys())}")
                        return None

                    # CORREÇÃO: Processar dados base64 mais cuidadosamente
                    media_base64 = None
                    if isinstance(media_data, str):
                        media_base64 = media_data
                    elif isinstance(media_data, dict):
                        # Procurar em diferentes campos possíveis
                        for field in ['media', 'buffer', 'data', 'content', 'file']:
                            if field in media_data:
                                media_base64 = media_data[field]
                                break

                    if not media_base64:
                        print(f"❌ String base64 não encontrada")
                        return None

                    # CORREÇÃO: Decodificação base64 mais robusta
                    try:
                        # Limpar dados base64
                        if media_base64.startswith('data:'):
                            media_base64 = media_base64.split(',', 1)[1]

                        # Remover espaços e quebras de linha
                        media_base64 = media_base64.strip().replace('\n', '').replace('\r', '').replace(' ', '')

                        # Validar caracteres base64
                        import re
                        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', media_base64):
                            print(f"❌ Caracteres inválidos na string base64")
                            return None

                        # Adicionar padding se necessário
                        padding = len(media_base64) % 4
                        if padding:
                            media_base64 += '=' * (4 - padding)

                        media_bytes = base64.b64decode(media_base64)

                        if len(media_bytes) == 0:
                            print(f"❌ Decodificação resultou em dados vazios")
                            return None

                        print(f"   ✅ Decodificado: {len(media_bytes)} bytes")

                    except Exception as e:
                        print(f"❌ Erro ao decodificar base64: {e}")
                        return None

                else:
                    # Resposta binária direta
                    media_bytes = response.content
                    if len(media_bytes) == 0:
                        print(f"❌ Resposta binária vazia")
                        return None
                    print(f"   ✅ Dados binários: {len(media_bytes)} bytes")

                # CORREÇÃO: Validação mais rigorosa de magic numbers
                if not self._validar_magic_numbers(media_bytes, info_midia['mimetype']):
                    print(f"❌ Arquivo corrompido - magic numbers inválidos")
                    return None

                # CORREÇÃO: Validar tamanho esperado se disponível
                if info_midia.get('fileLength'):
                    tamanho_esperado = int(info_midia['fileLength'])
                    tamanho_real = len(media_bytes)

                    # Tolerância de 10% ou 1KB (o que for maior)
                    tolerancia = max(1024, tamanho_esperado * 0.1)

                    if abs(tamanho_real - tamanho_esperado) > tolerancia:
                        print(f"❌ Tamanho incorreto - Esperado: {tamanho_esperado}, Real: {tamanho_real}")
                        return None

                # Gerar nome e salvar arquivo
                nome_arquivo = self.gerar_nome_arquivo(info_midia, message_id, sender_name)
                pasta_tipo = self.pastas_midia[info_midia['type']]
                caminho_arquivo = pasta_tipo / nome_arquivo

                # CORREÇÃO: Salvar arquivo de forma atômica
                caminho_temp = pasta_tipo / f"temp_{nome_arquivo}"

                try:
                    with open(caminho_temp, 'wb') as f:
                        f.write(media_bytes)

                    # Verificar se o arquivo temporário foi salvo corretamente
                    if caminho_temp.stat().st_size != len(media_bytes):
                        print(f"❌ Erro na gravação do arquivo")
                        caminho_temp.unlink(missing_ok=True)
                        return None

                    # Mover arquivo temporário para definitivo
                    caminho_temp.rename(caminho_arquivo)

                    print(f"✅ {info_midia['type'].title()} salvo: {caminho_arquivo}")

                    # NOVO: Atualizar vínculo na tabela de relacionamento
                    self._atualizar_vinculo_midia(message_id, info_midia['type'], str(caminho_arquivo))

                    return str(caminho_arquivo)

                except Exception as e:
                    print(f"❌ Erro ao salvar arquivo: {e}")
                    caminho_temp.unlink(missing_ok=True)
                    return None

            else:
                print(f"❌ Erro na API: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   📄 Detalhes: {error_detail}")
                except:
                    print(f"   📄 Resposta: {response.text[:200]}")
                return None

        except Exception as e:
            print(f"❌ Erro na descriptografia: {e}")
            return None

    def _atualizar_vinculo_midia(self, message_id: str, media_type: str, file_path: str):
        """Atualiza vínculo entre mensagem e mídia após download"""
        try:
            # Importar o database manager atualizado
            from backend.banco.database_manager_updated import WhatsAppDatabaseManager
            from backend.banco.models_updated import WebhookEvent

            db_manager = WhatsAppDatabaseManager(self.db_path)

            # Buscar event_id pelo message_id
            with db_manager.get_session() as session:
                event = session.query(WebhookEvent).filter_by(message_id=message_id).first()

                if event:
                    db_manager.update_media_path(event.id, media_type, file_path)
                    print(f"✅ Vínculo mídia atualizado: {media_type} -> {file_path}")

        except Exception as e:
            print(f"❌ Erro ao atualizar vínculo: {e}")

    def _validar_magic_numbers(self, data: bytes, mimetype: str) -> bool:
        """Valida magic numbers para verificar integridade do arquivo"""
        if len(data) < 12:  # Muito pequeno para ter magic numbers
            return False

        # Magic numbers mais específicos para áudios
        magic_numbers = {
            'audio/ogg': [b'OggS'],
            'audio/mpeg': [b'\xff\xfb', b'\xff\xf3', b'\xff\xf2', b'ID3'],
            'audio/mp4': [b'ftyp', b'ftypM4A'],
            'audio/wav': [b'RIFF'],
            'audio/webm': [b'\x1a\x45\xdf\xa3'],
            'image/jpeg': [b'\xff\xd8\xff'],
            'image/png': [b'\x89PNG\r\n\x1a\n'],
            'image/gif': [b'GIF87a', b'GIF89a'],
            'image/webp': [b'RIFF', b'WEBP'],
            'video/mp4': [b'ftyp', b'moov', b'mdat'],
            'video/webm': [b'\x1a\x45\xdf\xa3'],
            'video/3gpp': [b'ftyp3g'],
            'application/pdf': [b'%PDF']
        }

        expected_magic = magic_numbers.get(mimetype, [])
        if not expected_magic:
            print(f"   ⚠️ Magic number não definido para {mimetype}")
            return True  # Assumir válido se não soubermos o magic number

        # Verificar primeiros 20 bytes para magic numbers
        header = data[:20]

        for magic in expected_magic:
            if header.startswith(magic) or magic in header:
                print(f"   ✅ Magic number válido: {magic}")
                return True

        print(f"   ❌ Magic number inválido para {mimetype}")
        print(f"   📄 Header: {header}")
        return False

    def gerar_nome_arquivo(self, info_midia: Dict, message_id: str, sender_name: str) -> str:
        """Gera nome único para o arquivo - CORRIGIDO"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Limpar nome do remetente
        sender_clean = "".join(c for c in sender_name if c.isalnum() or c in (' ', '-', '_')).strip()
        sender_clean = sender_clean.replace(' ', '_')[:20]

        # CORREÇÃO: Obter extensão correta para áudios
        extensao = self._obter_extensao_correta(info_midia['mimetype'], info_midia.get('fileName'))

        # Se tem nome original, usar
        if info_midia.get('fileName'):
            nome_original = info_midia['fileName']
            nome_sem_ext = os.path.splitext(nome_original)[0][:30]
            return f"{timestamp}_{sender_clean}_{nome_sem_ext}{extensao}"

        # Senão, usar tipo e ID da mensagem
        tipo = info_midia['type']
        message_short = message_id[:8] if message_id else "unknown"

        return f"{timestamp}_{sender_clean}_{tipo}_{message_short}{extensao}"

    def _obter_extensao_correta(self, mimetype: str, filename: str = None) -> str:
        """Obtém extensão correta, priorizando filename original"""

        # Se tem filename original, usar sua extensão
        if filename and '.' in filename:
            ext_original = os.path.splitext(filename)[1].lower()
            if ext_original:
                return ext_original

        # CORREÇÃO: Mapeamento mais preciso de mimetypes
        mimetypes_map = {
            # Áudios - corrigidos
            'audio/ogg': '.ogg',
            'audio/ogg; codecs=opus': '.ogg',
            'audio/mpeg': '.mp3',
            'audio/mp4': '.m4a',
            'audio/wav': '.wav',
            'audio/webm': '.webm',
            'audio/aac': '.aac',
            'audio/flac': '.flac',

            # Imagens
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',

            # Vídeos
            'video/mp4': '.mp4',
            'video/webm': '.webm',
            'video/avi': '.avi',
            'video/mov': '.mov',
            'video/3gpp': '.3gp',
            'video/quicktime': '.mov',

            # Documentos
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'text/plain': '.txt'
        }

        return mimetypes_map.get(mimetype, '.bin')

    def processar_mensagem_whatsapp(self, data: Dict):
        """Processa mensagem e gerencia download de mídias - CORRIGIDO"""
        self.contador_mensagens += 1

        print('\n' + '🟢' * 70)
        print(f'📱 MENSAGEM #{self.contador_mensagens} - {datetime.now().strftime("%H:%M:%S")}')
        print('🟢' * 70)

        # Informações básicas
        message_id = data.get('messageId', 'N/A')
        sender = data.get('sender', {})
        sender_name = sender.get('pushName', 'Sem nome')

        print(f"🆔 Message ID: {message_id}")
        print(f"👤 DE: {sender_name}")

        # Processar conteúdo da mensagem
        msg_content = data.get('msgContent', {})

        if msg_content:
            # Verificar texto
            if 'conversation' in msg_content:
                print(f"\n💬 MENSAGEM: {msg_content['conversation']}")

            # Extrair e processar mídias
            midias_info = self.extrair_informacoes_midia(msg_content)

            if midias_info:
                print(f"\n📎 MÍDIA DETECTADA ({len(midias_info)} arquivo(s)):")

                for i, info_midia in enumerate(midias_info, 1):
                    self.contador_midias += 1

                    print(f"\n📄 Arquivo #{i}:")
                    print(f"   🎯 Tipo: {info_midia['type']}")
                    print(f"   📋 Mimetype: {info_midia['mimetype']}")

                    # CORREÇÃO: Validação mais rigorosa antes do download
                    if not self._validar_dados_midia(info_midia):
                        print(f"   ❌ Dados de mídia inválidos - pulando")
                        self.salvar_midia_no_banco(data, info_midia)  # Salvar como failed
                        self.atualizar_status_download(message_id, 'invalid_data')
                        continue

                    # Mostrar informações da mídia
                    if info_midia.get('fileName'):
                        print(f"   📄 Nome: {info_midia['fileName']}")

                    if info_midia.get('fileLength'):
                        size_mb = int(info_midia['fileLength']) / (1024 * 1024)
                        print(f"   📏 Tamanho: {size_mb:.2f} MB")

                    # Salvar no banco primeiro (como pendente)
                    self.salvar_midia_no_banco(data, info_midia)

                    # Tentar download apenas se configuração estiver completa
                    caminho_arquivo = None
                    if self.instance_id and self.bearer_token:
                        caminho_arquivo = self.descriptografar_e_baixar_midia(
                            info_midia, message_id, sender_name
                        )

                        # CORREÇÃO: Se falhar, tentar método alternativo com URL direta
                        if not caminho_arquivo and info_midia.get('url'):
                            print("   🔄 Tentando download direto da URL...")
                            caminho_arquivo = self._baixar_via_filelink(
                                info_midia['url'], info_midia, message_id, sender_name
                            )

                    # Atualizar status no banco
                    if caminho_arquivo:
                        self.atualizar_status_download(message_id, 'success', caminho_arquivo)
                        print(f"   ✅ Salvo: {caminho_arquivo}")

                        # CORREÇÃO: Validar arquivo salvo
                        if not self._validar_arquivo_final(Path(caminho_arquivo), info_midia):
                            print(f"   ⚠️ Arquivo pode estar corrompido")
                            self.atualizar_status_download(message_id, 'corrupted', caminho_arquivo)
                    else:
                        self.atualizar_status_download(message_id, 'failed')
                        print(f"   ❌ Falha no download")

        print('🟢' * 70 + '\n')

    def _validar_dados_midia(self, info_midia: Dict) -> bool:
        """Valida se os dados de mídia estão completos"""
        campos_obrigatorios = ['mediaKey', 'directPath', 'type', 'mimetype']

        for campo in campos_obrigatorios:
            if not info_midia.get(campo):
                print(f"   ❌ Campo obrigatório ausente: {campo}")
                return False

        # Validar se mediaKey tem formato válido (base64)
        media_key = info_midia['mediaKey']
        if len(media_key) < 32:  # MediaKey muito curta
            print(f"   ❌ MediaKey muito curta: {len(media_key)} chars")
            return False

        # Validar directPath
        direct_path = info_midia['directPath']
        if not direct_path.startswith('/'):
            print(f"   ❌ DirectPath inválido: {direct_path}")
            return False

        return True

    def _baixar_via_filelink(self, file_url: str, info_midia: Dict, message_id: str, sender_name: str) -> Optional[str]:
        """Baixa mídia usando URL direta fornecida pela API"""
        try:
            print(f"📥 Baixando via fileLink: {file_url[:50]}...")

            headers = {
                'Authorization': f'Bearer {self.bearer_token}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(file_url, headers=headers, stream=True, timeout=60)

            if response.status_code == 200:
                # Verificar se é o arquivo correto baseado no Content-Type
                content_type = response.headers.get('content-type', '').lower()
                expected_type = info_midia['mimetype'].lower()

                # Validação básica de tipo
                if 'audio' in expected_type and 'audio' not in content_type:
                    print(f"   ⚠️ Tipo de conteúdo inesperado: {content_type}")

                # Ler dados
                media_bytes = response.content

                if len(media_bytes) == 0:
                    print(f"❌ Arquivo vazio recebido")
                    return None

                # Validar magic numbers
                if not self._validar_magic_numbers(media_bytes, info_midia['mimetype']):
                    print(f"❌ Magic numbers inválidos para {info_midia['mimetype']}")
                    return None

                # Gerar nome e salvar arquivo
                nome_arquivo = self.gerar_nome_arquivo(info_midia, message_id, sender_name)
                pasta_tipo = self.pastas_midia[info_midia['type']]
                caminho_arquivo = pasta_tipo / nome_arquivo

                # Salvamento atômico
                caminho_temp = pasta_tipo / f"temp_{nome_arquivo}"

                with open(caminho_temp, 'wb') as f:
                    f.write(media_bytes)

                # Verificar se foi salvo corretamente
                if caminho_temp.stat().st_size != len(media_bytes):
                    print(f"❌ Erro na gravação do arquivo")
                    caminho_temp.unlink(missing_ok=True)
                    return None

                # Mover para definitivo
                caminho_temp.rename(caminho_arquivo)

                print(f"✅ {info_midia['type'].title()} baixado via fileLink: {caminho_arquivo}")
                return str(caminho_arquivo)
            else:
                print(f"❌ Erro no download via fileLink: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Erro no download via fileLink: {e}")
            return None

    def _validar_audio_final(self, caminho_arquivo: Path, info_midia: Dict) -> bool:
        """Validação específica para arquivos de áudio"""
        try:
            with open(caminho_arquivo, 'rb') as f:
                header = f.read(20)

            mimetype = info_midia['mimetype']

            # Validações específicas por tipo de áudio
            if 'ogg' in mimetype:
                if not header.startswith(b'OggS'):
                    print(f"   ❌ Header OGG inválido")
                    return False
            elif 'mpeg' in mimetype or mimetype == 'audio/mp3':
                # MP3 pode começar com ID3 tag ou frame sync
                if not (header.startswith(b'ID3') or
                        header[0:2] in [b'\xff\xfb', b'\xff\xf3', b'\xff\xf2']):
                    print(f"   ❌ Header MP3 inválido")
                    return False
            elif 'mp4' in mimetype or 'm4a' in mimetype:
                if not (b'ftyp' in header[:20]):
                    print(f"   ❌ Header M4A inválido")
                    return False
            elif 'wav' in mimetype:
                if not header.startswith(b'RIFF'):
                    print(f"   ❌ Header WAV inválido")
                    return False

            print(f"   ✅ Áudio validado com sucesso")
            return True

        except Exception as e:
            print(f"   ❌ Erro na validação de áudio: {e}")
            return False

    def validar_arquivo_baixado(self, caminho_arquivo: Path, info_midia: Dict) -> bool:
        """Valida se o arquivo baixado está íntegro"""
        if not caminho_arquivo.exists():
            return False

        # Verificar tamanho
        tamanho_real = caminho_arquivo.stat().st_size
        tamanho_esperado = info_midia.get('fileLength')

        if tamanho_esperado and abs(tamanho_real - int(tamanho_esperado)) > 1024:  # Tolerância de 1KB
            print(f"⚠️ Tamanho divergente - Esperado: {tamanho_esperado}, Real: {tamanho_real}")
            return False

        # Verificar magic numbers
        try:
            with open(caminho_arquivo, 'rb') as f:
                header = f.read(20)

            magic_numbers = {
                'image/jpeg': [b'\xff\xd8\xff'],
                'image/png': [b'\x89PNG'],
                'image/gif': [b'GIF87a', b'GIF89a'],
                'image/webp': [b'RIFF'],
                'audio/ogg': [b'OggS'],
                'audio/mpeg': [b'\xff\xfb', b'\xff\xf3', b'\xff\xf2', b'ID3'],
                'video/mp4': [b'ftyp', b'moov']
            }

            expected_magic = magic_numbers.get(info_midia['mimetype'], [])
            if expected_magic:
                is_valid = any(header.startswith(magic) or magic in header for magic in expected_magic)
                if not is_valid:
                    print(f"❌ Magic number inválido para {info_midia['mimetype']}")
                    return False

            return True

        except Exception as e:
            print(f"❌ Erro na validação: {e}")
            return False

    def baixar_midia_direta(self, info_midia: Dict, message_id: str, sender_name: str) -> Optional[str]:
        """Método alternativo usando URL direta quando disponível"""
        if not info_midia.get('url'):
            return None

        try:
            print(f"📥 Tentando download direto...")
            response = requests.get(info_midia['url'], timeout=30)

            if response.status_code == 200:
                nome_arquivo = self.gerar_nome_arquivo(info_midia, message_id, sender_name)
                pasta_tipo = self.pastas_midia[info_midia['type']]
                caminho_arquivo = pasta_tipo / nome_arquivo

                with open(caminho_arquivo, 'wb') as f:
                    f.write(response.content)

                print(f"✅ Download direto bem-sucedido: {caminho_arquivo}")
                return str(caminho_arquivo)
            else:
                return None

        except Exception as e:
            print(f"⚠️ Erro no download direto: {e}")
            return None

    def processar_mensagem_whatsapp(self, data: Dict):
        """Processa mensagem e gerencia download de mídias - CORRIGIDO"""
        self.contador_mensagens += 1

        print('\n' + '🟢' * 70)
        print(f'📱 MENSAGEM #{self.contador_mensagens} - {datetime.now().strftime("%H:%M:%S")}')
        print('🟢' * 70)

        # Informações básicas
        message_id = data.get('messageId', 'N/A')
        sender = data.get('sender', {})
        sender_name = sender.get('pushName', 'Sem nome')

        print(f"🆔 Message ID: {message_id}")
        print(f"👤 DE: {sender_name}")

        # Processar conteúdo da mensagem
        msg_content = data.get('msgContent', {})

        if msg_content:
            # Verificar texto
            if 'conversation' in msg_content:
                print(f"\n💬 MENSAGEM: {msg_content['conversation']}")

            # Extrair e processar mídias
            midias_info = self.extrair_informacoes_midia(msg_content)

            if midias_info:
                print(f"\n📎 MÍDIA DETECTADA ({len(midias_info)} arquivo(s)):")

                for i, info_midia in enumerate(midias_info, 1):
                    self.contador_midias += 1

                    print(f"\n📄 Arquivo #{i}:")
                    print(f"   🎯 Tipo: {info_midia['type']}")
                    print(f"   📋 Mimetype: {info_midia['mimetype']}")

                    # CORREÇÃO: Validação mais rigorosa antes do download
                    if not self._validar_dados_midia(info_midia):
                        print(f"   ❌ Dados de mídia inválidos - pulando")
                        self.salvar_midia_no_banco(data, info_midia)  # Salvar como failed
                        self.atualizar_status_download(message_id, 'invalid_data')
                        continue

                    # Mostrar informações da mídia
                    if info_midia.get('fileName'):
                        print(f"   📄 Nome: {info_midia['fileName']}")

                    if info_midia.get('fileLength'):
                        size_mb = int(info_midia['fileLength']) / (1024 * 1024)
                        print(f"   📏 Tamanho: {size_mb:.2f} MB")

                    # Salvar no banco primeiro (como pendente)
                    self.salvar_midia_no_banco(data, info_midia)

                    # Tentar download apenas se configuração estiver completa
                    caminho_arquivo = None
                    if self.instance_id and self.bearer_token:
                        caminho_arquivo = self.descriptografar_e_baixar_midia(
                            info_midia, message_id, sender_name
                        )

                    # Atualizar status no banco
                    if caminho_arquivo:
                        self.atualizar_status_download(message_id, 'success', caminho_arquivo)
                        print(f"   ✅ Salvo: {caminho_arquivo}")

                        # CORREÇÃO: Validar arquivo salvo
                        if not self._validar_arquivo_final(Path(caminho_arquivo), info_midia):
                            print(f"   ⚠️ Arquivo pode estar corrompido")
                            self.atualizar_status_download(message_id, 'corrupted', caminho_arquivo)
                    else:
                        self.atualizar_status_download(message_id, 'failed')
                        print(f"   ❌ Falha no download")

        print('🟢' * 70 + '\n')

    def _validar_arquivo_final(self, caminho_arquivo: Path, info_midia: Dict) -> bool:
        """Valida se o arquivo final está íntegro"""
        if not caminho_arquivo.exists():
            return False

        try:
            # Verificar se o arquivo não está vazio
            tamanho = caminho_arquivo.stat().st_size
            if tamanho == 0:
                print(f"   ❌ Arquivo vazio")
                return False

            # Para áudios, tentar abrir com validação básica
            if info_midia['type'] == 'audio':
                return self._validar_audio_final(caminho_arquivo, info_midia)

            # Para outros tipos, validar magic numbers
            with open(caminho_arquivo, 'rb') as f:
                header = f.read(20)

            return self._validar_magic_numbers(header, info_midia['mimetype'])

        except Exception as e:
            print(f"   ❌ Erro na validação final: {e}")
            return False

    def _validar_audio_final(self, caminho_arquivo: Path, info_midia: Dict) -> bool:
        """Validação específica para arquivos de áudio"""
        try:
            with open(caminho_arquivo, 'rb') as f:
                header = f.read(20)

            mimetype = info_midia['mimetype']

            # Validações específicas por tipo de áudio
            if 'ogg' in mimetype:
                if not header.startswith(b'OggS'):
                    print(f"   ❌ Header OGG inválido")
                    return False
            elif 'mpeg' in mimetype or mimetype == 'audio/mp3':
                # MP3 pode começar com ID3 tag ou frame sync
                if not (header.startswith(b'ID3') or
                        header[0:2] in [b'\xff\xfb', b'\xff\xf3', b'\xff\xf2']):
                    print(f"   ❌ Header MP3 inválido")
                    return False
            elif 'mp4' in mimetype or 'm4a' in mimetype:
                if not (b'ftyp' in header[:20]):
                    print(f"   ❌ Header M4A inválido")
                    return False
            elif 'wav' in mimetype:
                if not header.startswith(b'RIFF'):
                    print(f"   ❌ Header WAV inválido")
                    return False

            print(f"   ✅ Áudio validado com sucesso")
            return True

        except Exception as e:
            print(f"   ❌ Erro na validação de áudio: {e}")
            return False

    def _validar_dados_midia(self, info_midia: Dict) -> bool:
        """Valida se os dados de mídia estão completos"""
        campos_obrigatorios = ['mediaKey', 'directPath', 'type', 'mimetype']

        for campo in campos_obrigatorios:
            if not info_midia.get(campo):
                print(f"   ❌ Campo obrigatório ausente: {campo}")
                return False

        # Validar se mediaKey tem formato válido (base64)
        media_key = info_midia['mediaKey']
        if len(media_key) < 32:  # MediaKey muito curta
            print(f"   ❌ MediaKey muito curta: {len(media_key)} chars")
            return False

        # Validar directPath
        direct_path = info_midia['directPath']
        if not direct_path.startswith('/'):
            print(f"   ❌ DirectPath inválido: {direct_path}")
            return False

        return True

    def buscar_mensagens_novas(self) -> Optional[List[Dict]]:
        """Busca mensagens novas no webhook"""
        try:
            print(f"🔍 Consultando webhook: {self.webhook_id}")
            response = requests.get(self.webhook_id, timeout=10)

            print(f"📊 Status da resposta: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                requests_data = data.get('requests', [])

                print(f"📨 Total de requests no webhook: {len(requests_data)}")

                mensagens_novas = []

                for request in requests_data:
                    request_id = request.get('timestamp', '')

                    if request_id and request_id not in self.mensagens_processadas:
                        message_data = request.get('json') or request.get('data')

                        if message_data and self.eh_mensagem_whatsapp(message_data):
                            mensagens_novas.append({
                                'id': request_id,
                                'data': message_data
                            })
                            self.mensagens_processadas.add(request_id)

                print(f"✅ {len(mensagens_novas)} mensagens novas para processar")
                return mensagens_novas

            elif response.status_code == 404:
                print("❌ Webhook não encontrado ou expirado!")
                return None
            else:
                print(f"⚠️ Status inesperado: {response.status_code}")
                return []

        except Exception as e:
            print(f"⚠️ Erro ao buscar mensagens: {e}")
            return []

    def reprocessar_midias_pendentes(self):
        """Reprocessa mídias que falharam no download"""
        midias_pendentes = self.buscar_midias_pendentes()

        if not midias_pendentes:
            print("✅ Não há mídias pendentes para reprocessar")
            return

        print(f"🔄 Reprocessando {len(midias_pendentes)} mídias pendentes...")

        for midia in midias_pendentes:
            print(f"\n🔄 Reprocessando: {midia['media_type']} - {midia['sender_name']}")

            info_midia = {
                'type': midia['media_type'],
                'mediaKey': midia['media_key'],
                'directPath': midia['direct_path'],
                'mimetype': midia['mimetype'],
                'fileLength': midia['file_size'],
                'fileName': midia['file_name'],
                'caption': midia['caption'],
                'width': midia['width'],
                'height': midia['height'],
                'seconds': midia['duration_seconds']
            }

            caminho_arquivo = self.descriptografar_e_baixar_midia(
                info_midia, midia['message_id'], midia['sender_name']
            )

            if caminho_arquivo:
                self.atualizar_status_download(midia['message_id'], 'success', caminho_arquivo)
                print(f"✅ Reprocessado com sucesso")
            else:
                print(f"❌ Falha no reprocessamento")

    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas do banco de dados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total por tipo
                cursor.execute('''
                   SELECT media_type, COUNT(*) as total,
                          SUM(CASE WHEN download_status = 'success' THEN 1 ELSE 0 END) as sucesso,
                          SUM(CASE WHEN download_status = 'failed' THEN 1 ELSE 0 END) as falhas,
                          SUM(CASE WHEN download_status = 'pending' THEN 1 ELSE 0 END) as pendentes
                   FROM whatsapp_midias 
                   GROUP BY media_type
               ''')

                estatisticas = {}
                for row in cursor.fetchall():
                    tipo, total, sucesso, falhas, pendentes = row
                    estatisticas[tipo] = {
                        'total': total,
                        'sucesso': sucesso,
                        'falhas': falhas,
                        'pendentes': pendentes
                    }

                return estatisticas

        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return {}

    def monitorar_com_processamento_automatico(self):
        """Monitor principal com processamento automático"""
        print(f"\n🚀 MONITOR WHATSAPP COM PROCESSAMENTO AUTOMÁTICO")
        print("=" * 60)
        print(f"🔗 Webhook: {self.webhook_id}")
        print(f"📱 Instance: {self.instance_id}")
        print(f"📁 Downloads: {self.pasta_downloads}")
        print(f"🗄️ Banco: {self.db_path}")
        print(f"✅ Descriptografia e download automático ATIVO")
        print("💡 Pressione Ctrl+C para parar")
        print("🔄 Verificando a cada 3 segundos...\n")

        inicio = datetime.now()

        try:
            while True:
                mensagens_novas = self.buscar_mensagens_novas()

                if mensagens_novas is None:
                    print("❌ Webhook não encontrado ou expirado!")
                    break

                if mensagens_novas:
                    print(f"📨 {len(mensagens_novas)} mensagens novas encontradas")
                    for msg in mensagens_novas:
                        self.processar_mensagem_whatsapp(msg['data'])
                else:
                    # Mostrar que está monitorando
                    print("🔍 Monitorando... (sem novas mensagens)", end='\r')

                # Status periódico a cada minuto
                tempo_ativo = datetime.now() - inicio
                if tempo_ativo.seconds > 0 and tempo_ativo.seconds % 60 == 0:
                    estatisticas = self.obter_estatisticas()
                    total_midias = sum(stats['total'] for stats in estatisticas.values()) if estatisticas else 0
                    total_sucesso = sum(stats['sucesso'] for stats in estatisticas.values()) if estatisticas else 0

                    print(f"\n⏱️ Ativo há {tempo_ativo.seconds // 60}min | "
                          f"Mensagens: {self.contador_mensagens} | "
                          f"Mídias: {total_midias} | "
                          f"Downloads: {total_sucesso}")

                time.sleep(3)

        except KeyboardInterrupt:
            tempo_total = datetime.now() - inicio
            estatisticas = self.obter_estatisticas()

            print(f"\n\n👋 MONITORAMENTO PARADO!")
            print(f"📊 Tempo ativo: {tempo_total.seconds // 60}min {tempo_total.seconds % 60}s")
            print(f"📊 Mensagens processadas: {self.contador_mensagens}")

            if estatisticas:
                print(f"📊 Estatísticas por tipo:")
                for tipo, stats in estatisticas.items():
                    print(f"   {tipo}: {stats['sucesso']}/{stats['total']} downloads")

            print(f"📁 Downloads em: {self.pasta_downloads}")
            print(f"🗄️ Banco: {self.db_path}")

        except Exception as e:
            print(f"\n❌ Erro durante monitoramento: {e}")
            import traceback
            traceback.print_exc()

    def executar(self):
        """Ponto de entrada principal"""
        print("📎 WHATSAPP MEDIA MANAGER")
        print("=" * 40)
        print("🎯 Descriptografia e download automático de mídias")
        print("🗄️ Gerenciamento via banco de dados")

        if not self.instance_id or not self.bearer_token:
            print("❌ Configuração incompleta. Forneça instance_id e bearer_token.")
            return

        print(f"\n✅ Webhook: {self.webhook_id}")
        print("🔧 API configurada - processamento automático ATIVO")

        # Reprocessar mídias pendentes antes de iniciar monitoramento
        print("\n🔄 Verificando mídias pendentes...")
        self.reprocessar_midias_pendentes()

        # Iniciar monitoramento - ESTA LINHA ESTAVA FALTANDO NO CÓDIGO ANTERIOR
        self.monitorar_com_processamento_automatico()


if __name__ == '__main__':
    try:
        # Configurações
        INSTANCE_ID = "3B6XIW-ZTS923-GEAY6V"
        BEARER_TOKEN = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"
        WEBHOOK_URL = "https://dream-photographs-tom-demographic.trycloudflare.com/requests?limit=100"

        # Inicializar manager
        manager = BaixarMidias(
            webhook_id=WEBHOOK_URL,
            instance_id=INSTANCE_ID,
            bearer_token=BEARER_TOKEN,
        )

        manager.executar()

    except KeyboardInterrupt:
        print("\n👋 Manager encerrado!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

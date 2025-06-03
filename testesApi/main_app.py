#!/usr/bin/env python3
"""
Interface de Atendimento Comercial - WhatsApp Business
Integrada com W-API e Monitor de Webhook
"""

import sys
import json
import requests
import time
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QPushButton,
    QLabel, QFrame, QScrollArea, QSplitter, QHeaderView, QToolBar,
    QStatusBar, QMessageBox, QDialog, QFormLayout, QComboBox,
    QProgressBar, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import (
    QFont, QPalette, QColor, QPixmap, QIcon, QAction,
    QPainter, QPen, QBrush
)


class WebhookMonitor(QThread):
    """Thread para monitorar o webhook em segundo plano"""

    nova_mensagem = pyqtSignal(dict)  # Sinal para nova mensagem
    status_changed = pyqtSignal(str)  # Sinal para mudança de status

    def __init__(self, webhook_id):
        super().__init__()
        self.webhook_id = webhook_id
        self.mensagens_processadas = set()
        self.ultima_verificacao = None
        self.running = False

    def run(self):
        """Executa o monitoramento contínuo"""
        self.running = True
        self.status_changed.emit("Conectado")

        while self.running:
            try:
                mensagens_novas = self.buscar_mensagens_novas()

                if mensagens_novas:
                    for msg in mensagens_novas:
                        self.nova_mensagem.emit(msg['data'])

                time.sleep(3)  # Verifica a cada 3 segundos

            except Exception as e:
                self.status_changed.emit(f"Erro: {str(e)[:20]}")
                time.sleep(10)  # Espera mais tempo se houver erro

    def stop(self):
        """Para o monitoramento"""
        self.running = False
        self.status_changed.emit("Desconectado")

    def buscar_mensagens_novas(self):
        """Busca mensagens novas no webhook"""
        try:
            url = f"https://webhook.site/token/{self.webhook_id}/requests"
            response = requests.get(url, timeout=5)

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
                                        'data': message_data,
                                        'timestamp': request.get('created_at', '')
                                    })
                                    self.mensagens_processadas.add(request_id)
                            except json.JSONDecodeError:
                                pass

                self.ultima_verificacao = datetime.now()
                return mensagens_novas

            return []

        except Exception as e:
            print(f"Erro ao buscar mensagens: {e}")
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


class WAPIClient:
    """Cliente para a W-API"""

    def __init__(self, instance_id, token):
        self.instance_id = instance_id
        self.token = token
        self.base_url = "https://api.w-api.app/v1"
        self.headers = {"Authorization": f"Bearer {token}"}

    def buscar_chats(self, per_page=20, page=1):
        """Busca lista de chats da W-API"""
        try:
            url = f"{self.base_url}/chats/fetch-chats"
            params = {
                "instanceId": self.instance_id,
                "perPage": per_page,
                "page": page
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro ao buscar chats: {response.status_code}")
                return None

        except Exception as e:
            print(f"Erro na requisição: {e}")
            return None

    def enviar_mensagem(self, chat_id, mensagem):
        """Envia mensagem via W-API"""
        try:
            url = f"{self.base_url}/messages/send-text"
            data = {
                "instanceId": self.instance_id,
                "chatId": chat_id,
                "text": mensagem
            }

            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            return response.status_code == 200

        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            return False


class ConversaItem(QWidget):
    """Widget personalizado para item da lista de conversas"""

    def __init__(self, nome, ultima_mensagem, horario, chat_id, nao_lidas=0):
        super().__init__()
        self.nome = nome
        self.chat_id = chat_id
        self.nao_lidas = nao_lidas
        self.setup_ui(nome, ultima_mensagem, horario, nao_lidas)

    def setup_ui(self, nome, ultima_mensagem, horario, nao_lidas):
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)

        # Avatar (círculo colorido com inicial)
        avatar = QLabel()
        avatar.setFixedSize(50, 50)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: #25D366;
                border-radius: 25px;
                color: white;
                font-weight: bold;
                font-size: 18px;
            }}
        """)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setText(nome[0].upper() if nome else "?")

        # Informações da conversa
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Linha superior: Nome e horário
        linha_superior = QHBoxLayout()
        linha_superior.setContentsMargins(0, 0, 0, 0)

        label_nome = QLabel(nome)
        label_nome.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        label_nome.setStyleSheet("color: #000000;")

        label_horario = QLabel(horario)
        label_horario.setFont(QFont("Segoe UI", 9))
        label_horario.setStyleSheet("color: #667781;")
        label_horario.setAlignment(Qt.AlignmentFlag.AlignRight)

        linha_superior.addWidget(label_nome)
        linha_superior.addStretch()
        linha_superior.addWidget(label_horario)

        # Linha inferior: Última mensagem e contador
        linha_inferior = QHBoxLayout()
        linha_inferior.setContentsMargins(0, 0, 0, 0)

        label_mensagem = QLabel(ultima_mensagem)
        label_mensagem.setFont(QFont("Segoe UI", 9))
        label_mensagem.setStyleSheet("color: #667781;")
        label_mensagem.setWordWrap(True)

        # Contador de mensagens não lidas
        if nao_lidas > 0:
            contador = QLabel(str(nao_lidas))
            contador.setFixedSize(20, 20)
            contador.setStyleSheet("""
                QLabel {
                    background-color: #25D366;
                    border-radius: 10px;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            contador.setAlignment(Qt.AlignmentFlag.AlignCenter)
            linha_inferior.addWidget(label_mensagem)
            linha_inferior.addStretch()
            linha_inferior.addWidget(contador)
        else:
            linha_inferior.addWidget(label_mensagem)

        info_layout.addLayout(linha_superior)
        info_layout.addLayout(linha_inferior)

        layout.addWidget(avatar)
        layout.addLayout(info_layout, 1)

        self.setLayout(layout)
        self.setFixedHeight(80)

        # Estilo hover
        self.setStyleSheet("""
            ConversaItem:hover {
                background-color: #F5F6F6;
            }
        """)


class MensagemWidget(QWidget):
    """Widget para exibir uma mensagem individual"""

    def __init__(self, texto, enviada_por_mim=False, horario="", tipo_midia=None, sender_name=""):
        super().__init__()
        self.enviada_por_mim = enviada_por_mim
        self.setup_ui(texto, horario, tipo_midia, sender_name)

    def setup_ui(self, texto, horario, tipo_midia, sender_name):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        # Container da mensagem
        container = QFrame()
        container.setMaximumWidth(400)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(12, 8, 12, 8)
        container_layout.setSpacing(4)

        # Nome do remetente (apenas para mensagens recebidas)
        if not self.enviada_por_mim and sender_name:
            label_sender = QLabel(sender_name)
            label_sender.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            label_sender.setStyleSheet("color: #25D366;")
            container_layout.addWidget(label_sender)

        # Ícone de mídia se houver
        if tipo_midia:
            icone_midia = QLabel()
            if tipo_midia == "image":
                icone_midia.setText("🖼️ Imagem")
            elif tipo_midia == "video":
                icone_midia.setText("🎥 Vídeo")
            elif tipo_midia == "audio":
                icone_midia.setText("🎵 Áudio")
            elif tipo_midia == "document":
                icone_midia.setText("📄 Documento")

            icone_midia.setFont(QFont("Segoe UI", 9))
            icone_midia.setStyleSheet("color: #667781; font-style: italic;")
            container_layout.addWidget(icone_midia)

        # Texto da mensagem
        if texto:
            label_texto = QLabel(texto)
            label_texto.setWordWrap(True)
            label_texto.setFont(QFont("Segoe UI", 10))
            container_layout.addWidget(label_texto)

        # Horário
        if horario:
            label_horario = QLabel(horario)
            label_horario.setFont(QFont("Segoe UI", 8))
            label_horario.setStyleSheet("color: #667781;")
            label_horario.setAlignment(Qt.AlignmentFlag.AlignRight)
            container_layout.addWidget(label_horario)

        container.setLayout(container_layout)

        # Estilo baseado em quem enviou
        if self.enviada_por_mim:
            container.setStyleSheet("""
                QFrame {
                    background-color: #DCF8C6;
                    border-radius: 8px;
                    border: none;
                }
            """)
            layout.addStretch()
            layout.addWidget(container)
        else:
            container.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border-radius: 8px;
                    border: 1px solid #E0E0E0;
                }
            """)
            layout.addWidget(container)
            layout.addStretch()

        self.setLayout(layout)


class AreaChat(QWidget):
    """Área principal do chat"""

    def __init__(self, wapi_client=None):
        super().__init__()
        self.conversa_atual = None
        self.wapi_client = wapi_client
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header do chat
        self.header = QFrame()
        self.header.setFixedHeight(70)
        self.header.setStyleSheet("""
            QFrame {
                background-color: #F0F2F5;
                border-bottom: 1px solid #E0E0E0;
            }
        """)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 10, 20, 10)

        # Avatar do contato
        self.avatar_contato = QLabel()
        self.avatar_contato.setFixedSize(45, 45)
        self.avatar_contato.setStyleSheet("""
            QLabel {
                background-color: #25D366;
                border-radius: 22px;
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        self.avatar_contato.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Info do contato
        info_contato = QVBoxLayout()
        info_contato.setSpacing(2)

        self.nome_contato = QLabel("Selecione uma conversa")
        self.nome_contato.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

        self.status_contato = QLabel("")
        self.status_contato.setFont(QFont("Segoe UI", 9))
        self.status_contato.setStyleSheet("color: #667781;")

        info_contato.addWidget(self.nome_contato)
        info_contato.addWidget(self.status_contato)

        header_layout.addWidget(self.avatar_contato)
        header_layout.addLayout(info_contato)
        header_layout.addStretch()

        self.header.setLayout(header_layout)

        # Área de mensagens
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #E5DDD5;
                border: none;
            }
        """)

        self.mensagens_widget = QWidget()
        self.mensagens_layout = QVBoxLayout()
        self.mensagens_layout.setContentsMargins(0, 10, 0, 10)
        self.mensagens_layout.setSpacing(5)
        self.mensagens_widget.setLayout(self.mensagens_layout)

        self.scroll_area.setWidget(self.mensagens_widget)

        # Área de input
        input_frame = QFrame()
        input_frame.setFixedHeight(70)
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #F0F2F5;
                border-top: 1px solid #E0E0E0;
            }
        """)

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(15, 10, 15, 10)

        # Campo de texto
        self.input_mensagem = QLineEdit()
        self.input_mensagem.setPlaceholderText("Digite uma mensagem...")
        self.input_mensagem.setFont(QFont("Segoe UI", 11))
        self.input_mensagem.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 20px;
                padding: 10px 15px;
            }
            QLineEdit:focus {
                border: 1px solid #25D366;
            }
        """)

        # Botão enviar
        self.btn_enviar = QPushButton("Enviar")
        self.btn_enviar.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_enviar.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #20BD5F;
            }
            QPushButton:pressed {
                background-color: #1FAD58;
            }
        """)

        input_layout.addWidget(self.input_mensagem)
        input_layout.addWidget(self.btn_enviar)
        input_frame.setLayout(input_layout)

        # Conectar eventos
        self.input_mensagem.returnPressed.connect(self.enviar_mensagem)
        self.btn_enviar.clicked.connect(self.enviar_mensagem)

        layout.addWidget(self.header)
        layout.addWidget(self.scroll_area, 1)
        layout.addWidget(input_frame)

        self.setLayout(layout)

    def carregar_conversa(self, nome, chat_id):
        """Carrega uma conversa específica"""
        self.conversa_atual = {"nome": nome, "chat_id": chat_id}

        # Atualizar header
        self.nome_contato.setText(nome)
        self.status_contato.setText(chat_id)
        self.avatar_contato.setText(nome[0].upper() if nome else "?")

        # Limpar mensagens anteriores
        self.limpar_mensagens()

        # Adicionar mensagem de início da conversa
        self.adicionar_mensagem(
            f"Conversa iniciada com {nome}",
            False,
            datetime.now().strftime("%H:%M"),
            sender_name="Sistema"
        )

    def processar_mensagem_webhook(self, data):
        """Processa mensagem recebida do webhook"""
        try:
            # Extrair informações da mensagem
            sender = data.get('sender', {})
            sender_name = sender.get('pushName', sender.get('name', 'Contato'))
            chat = data.get('chat', {})
            chat_id = chat.get('id', '')
            from_me = data.get('fromMe', False)

            # Verificar se é da conversa atual
            if self.conversa_atual and chat_id == self.conversa_atual['chat_id']:
                # Extrair texto da mensagem
                texto = self.extrair_texto_mensagem(data)
                tipo_midia = self.extrair_tipo_midia(data)

                # Extrair timestamp
                moment = data.get('moment', data.get('timestamp'))
                horario = ""
                if moment:
                    try:
                        if isinstance(moment, (int, float)):
                            dt = datetime.fromtimestamp(moment)
                            horario = dt.strftime("%H:%M")
                    except:
                        horario = datetime.now().strftime("%H:%M")

                # Adicionar mensagem
                self.adicionar_mensagem(
                    texto or "",
                    from_me,
                    horario,
                    tipo_midia,
                    sender_name if not from_me else ""
                )

        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")

    def extrair_texto_mensagem(self, data):
        """Extrai o texto da mensagem dos dados do webhook"""
        msg_content = data.get('msgContent', data.get('message', data.get('content', {})))

        # Tentar campo 'text' diretamente
        if data.get('text'):
            return data.get('text')

        # Tentar campo 'body' diretamente
        if data.get('body'):
            return data.get('body')

        if isinstance(msg_content, str):
            return msg_content
        elif isinstance(msg_content, dict):
            if 'conversation' in msg_content:
                return msg_content['conversation']
            elif 'text' in msg_content:
                return msg_content['text']

        return None

    def extrair_tipo_midia(self, data):
        """Extrai o tipo de mídia da mensagem"""
        msg_content = data.get('msgContent', data.get('message', data.get('content', {})))

        if isinstance(msg_content, dict):
            if 'imageMessage' in msg_content:
                return 'image'
            elif 'videoMessage' in msg_content:
                return 'video'
            elif 'audioMessage' in msg_content:
                return 'audio'
            elif 'documentMessage' in msg_content:
                return 'document'

        return None

    def limpar_mensagens(self):
        """Remove todas as mensagens da área de chat"""
        while self.mensagens_layout.count():
            child = self.mensagens_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def adicionar_mensagem(self, texto, enviada_por_mim=True, horario="", tipo_midia=None, sender_name=""):
        """Adiciona uma nova mensagem ao chat"""
        if not horario:
            horario = datetime.now().strftime("%H:%M")

        mensagem = MensagemWidget(texto, enviada_por_mim, horario, tipo_midia, sender_name)
        self.mensagens_layout.addWidget(mensagem)

        # Scroll para baixo
        QTimer.singleShot(100, self.scroll_para_baixo)

    def scroll_para_baixo(self):
        """Faz scroll para a última mensagem"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def enviar_mensagem(self):
        """Envia uma nova mensagem"""
        texto = self.input_mensagem.text().strip()
        if not texto or not self.conversa_atual:
            return

        # Adicionar mensagem na interface
        self.adicionar_mensagem(texto, True)

        # Enviar via W-API se disponível
        if self.wapi_client:
            sucesso = self.wapi_client.enviar_mensagem(
                self.conversa_atual['chat_id'],
                texto
            )
            if not sucesso:
                self.adicionar_mensagem(
                    "❌ Erro ao enviar mensagem",
                    False,
                    datetime.now().strftime("%H:%M"),
                    sender_name="Sistema"
                )

        # Limpar input
        self.input_mensagem.clear()


class ListaConversas(QListWidget):
    """Lista de conversas personalizada"""

    conversa_selecionada = pyqtSignal(str, str)  # nome, chat_id

    def __init__(self, wapi_client=None):
        super().__init__()
        self.wapi_client = wapi_client
        self.setup_ui()
        self.carregar_chats()

    def setup_ui(self):
        self.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #F0F2F5;
                padding: 0px;
            }
            QListWidget::item:selected {
                background-color: #E7F3FF;
            }
            QListWidget::item:hover {
                background-color: #F5F6F6;
            }
        """)

        self.itemClicked.connect(self.on_conversa_clicada)

    def carregar_chats(self):
        """Carrega chats da W-API"""
        if not self.wapi_client:
            self.carregar_conversas_exemplo()
            return

        try:
            dados = self.wapi_client.buscar_chats(per_page=50)

            if dados and 'chats' in dados:
                self.clear()  # Limpar lista anterior

                for chat in dados['chats']:
                    nome = chat.get('name') or 'Sem Nome'
                    chat_id = chat.get('id')

                    # Converter timestamp para horário legível
                    last_msg_time = chat.get('lastMessageTime')
                    horario = ""
                    if last_msg_time:
                        try:
                            dt = datetime.fromtimestamp(last_msg_time)
                            horario = dt.strftime("%H:%M")
                        except:
                            horario = "N/A"

                    self.adicionar_conversa(
                        nome,
                        chat_id,
                        "Última mensagem...",  # Poderia buscar a última mensagem
                        horario,
                        0  # Número de não lidas (não disponível na API atual)
                    )
            else:
                self.carregar_conversas_exemplo()

        except Exception as e:
            print(f"Erro ao carregar chats: {e}")
            self.carregar_conversas_exemplo()

    def carregar_conversas_exemplo(self):
        """Carrega conversas de exemplo se não conseguir da API"""
        conversas = [
            {"nome": "𝓣𝓱𝓪𝔂𝓷𝓪🍃", "chat_id": "556999267344@s.whatsapp.net", "ultima_msg": "Caracas isso é muit9 bom",
             "horario": "00:03", "nao_lidas": 2},
            {"nome": "João Silva", "chat_id": "5511987654321@s.whatsapp.net",
             "ultima_msg": "Obrigado pelo atendimento!", "horario": "23:45", "nao_lidas": 0},
            {"nome": "Maria Santos", "chat_id": "5511876543210@s.whatsapp.net",
             "ultima_msg": "Quando vocês abrem amanhã?", "horario": "22:30", "nao_lidas": 1},
        ]

        for conversa in conversas:
            self.adicionar_conversa(
                conversa["nome"],
                conversa["chat_id"],
                conversa["ultima_msg"],
                conversa["horario"],
                conversa["nao_lidas"]
            )

    def adicionar_conversa(self, nome, chat_id, ultima_msg, horario, nao_lidas=0):
        """Adiciona uma nova conversa à lista"""
        item = QListWidgetItem()
        widget = ConversaItem(nome, ultima_msg, horario, chat_id, nao_lidas)

        item.setSizeHint(widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, widget)

    def on_conversa_clicada(self, item):
        """Callback quando uma conversa é clicada"""
        widget = self.itemWidget(item)
        if widget:
            self.conversa_selecionada.emit(widget.nome, widget.chat_id)

    def atualizar_conversa(self, chat_id, nova_mensagem):
        """Atualiza uma conversa com nova mensagem"""
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget and widget.chat_id == chat_id:
                # Aqui poderia atualizar a última mensagem e horário
                break


class ConfiguracaoDialog(QDialog):
    """Dialog para configuração da W-API e Webhook"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Configurações")
        self.setFixedSize(500, 400)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        titulo = QLabel("Configurações do Sistema")
        titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("color: #25D366; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # Abas de configuração
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                margin-top: 5px;
            }
            QTabBar::tab {
                background-color: #F0F2F5;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #25D366;
                color: white;
            }
        """)

        # Aba W-API
        wapi_tab = QWidget()
        wapi_layout = QVBoxLayout()
        wapi_layout.setSpacing(15)

        # Seção Instance ID
        instance_group = QFrame()
        instance_group.setStyleSheet("QFrame { border: 1px solid #E0E0E0; border-radius: 5px; padding: 10px; }")
        instance_layout = QVBoxLayout()

        instance_label = QLabel("Instance ID")
        instance_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        self.instance_id_input = QLineEdit()
        self.instance_id_input.setText("3B6XIW-ZTS923-GEAY6V")
        self.instance_id_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
            }
            QLineEdit:focus {
                border: 2px solid #25D366;
            }
        """)

        instance_layout.addWidget(instance_label)
        instance_layout.addWidget(self.instance_id_input)
        instance_group.setLayout(instance_layout)

        # Seção Token
        token_group = QFrame()
        token_group.setStyleSheet("QFrame { border: 1px solid #E0E0E0; border-radius: 5px; padding: 10px; }")
        token_layout = QVBoxLayout()

        token_label = QLabel("Token de Acesso")
        token_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        self.token_input = QLineEdit()
        self.token_input.setText("Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
            }
            QLineEdit:focus {
                border: 2px solid #25D366;
            }
        """)

        # Botão para mostrar/ocultar token
        self.btn_mostrar_token = QPushButton("👁️ Mostrar")
        self.btn_mostrar_token.setFixedWidth(80)
        self.btn_mostrar_token.clicked.connect(self.toggle_token_visibility)
        self.btn_mostrar_token.setStyleSheet("""
            QPushButton {
                background-color: #F0F2F5;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)

        token_input_layout = QHBoxLayout()
        token_input_layout.addWidget(self.token_input)
        token_input_layout.addWidget(self.btn_mostrar_token)

        token_layout.addWidget(token_label)
        token_layout.addLayout(token_input_layout)
        token_group.setLayout(token_layout)

        # Informações adicionais
        info_label = QLabel("ℹ️ Estas credenciais são usadas para acessar a W-API")
        info_label.setStyleSheet("color: #667781; font-style: italic; margin-top: 10px;")

        wapi_layout.addWidget(instance_group)
        wapi_layout.addWidget(token_group)
        wapi_layout.addWidget(info_label)
        wapi_layout.addStretch()

        wapi_tab.setLayout(wapi_layout)
        tabs.addTab(wapi_tab, "🔌 W-API")

        # Aba Webhook
        webhook_tab = QWidget()
        webhook_layout = QVBoxLayout()
        webhook_layout.setSpacing(15)

        # Seção Webhook ID
        webhook_group = QFrame()
        webhook_group.setStyleSheet("QFrame { border: 1px solid #E0E0E0; border-radius: 5px; padding: 10px; }")
        webhook_group_layout = QVBoxLayout()

        webhook_label = QLabel("Webhook ID")
        webhook_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        self.webhook_id_input = QLineEdit()
        self.webhook_id_input.setText("0e6e92fd-c357-44e4-b1e5-067d6ae4cd0d")
        self.webhook_id_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
            }
            QLineEdit:focus {
                border: 2px solid #25D366;
            }
        """)

        webhook_group_layout.addWidget(webhook_label)
        webhook_group_layout.addWidget(self.webhook_id_input)
        webhook_group.setLayout(webhook_group_layout)

        # Instruções do Webhook
        instrucoes_webhook = QLabel("""
📋 <b>Como configurar o Webhook:</b><br><br>
1. Acesse <a href="https://webhook.site">webhook.site</a><br>
2. Copie o ID que aparece na URL<br>
3. Configure na W-API para enviar para o webhook<br>
4. Cole o ID aqui
        """)
        instrucoes_webhook.setOpenExternalLinks(True)
        instrucoes_webhook.setWordWrap(True)
        instrucoes_webhook.setStyleSheet("""
            QLabel {
                background-color: #F8F9FA;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                padding: 15px;
                color: #333;
            }
        """)

        webhook_layout.addWidget(webhook_group)
        webhook_layout.addWidget(instrucoes_webhook)
        webhook_layout.addStretch()

        webhook_tab.setLayout(webhook_layout)
        tabs.addTab(webhook_tab, "🔗 Webhook")

        # Aba Avançado
        avancado_tab = QWidget()
        avancado_layout = QVBoxLayout()
        avancado_layout.setSpacing(15)

        # Configurações de tempo
        tempo_group = QFrame()
        tempo_group.setStyleSheet("QFrame { border: 1px solid #E0E0E0; border-radius: 5px; padding: 10px; }")
        tempo_layout = QVBoxLayout()

        tempo_label = QLabel("Configurações de Tempo")
        tempo_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        # Intervalo de verificação do webhook
        intervalo_layout = QHBoxLayout()
        intervalo_layout.addWidget(QLabel("Intervalo de verificação:"))

        self.intervalo_input = QComboBox()
        self.intervalo_input.addItems(["1 segundo", "3 segundos", "5 segundos", "10 segundos"])
        self.intervalo_input.setCurrentText("3 segundos")

        intervalo_layout.addWidget(self.intervalo_input)
        intervalo_layout.addStretch()

        tempo_layout.addWidget(tempo_label)
        tempo_layout.addLayout(intervalo_layout)
        tempo_group.setLayout(tempo_layout)

        # Configurações de exibição
        exibicao_group = QFrame()
        exibicao_group.setStyleSheet("QFrame { border: 1px solid #E0E0E0; border-radius: 5px; padding: 10px; }")
        exibicao_layout = QVBoxLayout()

        exibicao_label = QLabel("Configurações de Exibição")
        exibicao_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        # Máximo de conversas
        max_conversas_layout = QHBoxLayout()
        max_conversas_layout.addWidget(QLabel("Máximo de conversas:"))

        self.max_conversas_input = QComboBox()
        self.max_conversas_input.addItems(["20", "50", "100", "200"])
        self.max_conversas_input.setCurrentText("50")

        max_conversas_layout.addWidget(self.max_conversas_input)
        max_conversas_layout.addStretch()

        exibicao_layout.addWidget(exibicao_label)
        exibicao_layout.addLayout(max_conversas_layout)
        exibicao_group.setLayout(exibicao_layout)

        avancado_layout.addWidget(tempo_group)
        avancado_layout.addWidget(exibicao_group)
        avancado_layout.addStretch()

        avancado_tab.setLayout(avancado_layout)
        tabs.addTab(avancado_tab, "⚙️ Avançado")

        layout.addWidget(tabs)

        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Botão de testar
        btn_testar = QPushButton("🔍 Testar Conexão")
        btn_testar.clicked.connect(self.testar_conexao)
        btn_testar.setStyleSheet("""
            QPushButton {
                background-color: #17A2B8;
                color: white;
                font-weight: bold;
                padding: 10px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)

        # Botão de restaurar padrões
        btn_restaurar = QPushButton("🔄 Restaurar Padrões")
        btn_restaurar.clicked.connect(self.restaurar_padroes)
        btn_restaurar.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                font-weight: bold;
                padding: 10px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
        """)

        # Botão cancelar
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;
                color: white;
                font-weight: bold;
                padding: 10px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
        """)

        # Botão salvar
        btn_salvar = QPushButton("💾 Salvar")
        btn_salvar.clicked.connect(self.accept)
        btn_salvar.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                font-weight: bold;
                padding: 10px 15px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #20BD5F;
            }
        """)

        buttons_layout.addWidget(btn_testar)
        buttons_layout.addWidget(btn_restaurar)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_cancelar)
        buttons_layout.addWidget(btn_salvar)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def toggle_token_visibility(self):
        """Alterna visibilidade do token"""
        if self.token_input.echoMode() == QLineEdit.EchoMode.Password:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_mostrar_token.setText("🙈 Ocultar")
        else:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_mostrar_token.setText("👁️ Mostrar")

    def restaurar_padroes(self):
        """Restaura configurações padrão"""
        resposta = QMessageBox.question(
            self,
            "Restaurar Padrões",
            "Tem certeza que deseja restaurar as configurações padrão?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resposta == QMessageBox.StandardButton.Yes:
            self.instance_id_input.setText("3B6XIW-ZTS923-GEAY6V")
            self.token_input.setText("Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF")
            self.webhook_id_input.setText("0e6e92fd-c357-44e4-b1e5-067d6ae4cd0d")
            self.intervalo_input.setCurrentText("3 segundos")
            self.max_conversas_input.setCurrentText("50")

            QMessageBox.information(self, "Sucesso", "Configurações padrão restauradas!")

    def testar_conexao(self):
        """Testa a conexão com W-API"""
        instance_id = self.instance_id_input.text().strip()
        token = self.token_input.text().strip()

        if not instance_id or not token:
            QMessageBox.warning(self, "Erro", "Preencha Instance ID e Token!")
            return

        # Criar barra de progresso
        progress = QProgressBar()
        progress.setRange(0, 0)  # Indeterminado

        # Dialog de teste
        test_dialog = QDialog(self)
        test_dialog.setWindowTitle("Testando Conexão")
        test_dialog.setFixedSize(300, 100)

        test_layout = QVBoxLayout()
        test_layout.addWidget(QLabel("Testando conexão com W-API..."))
        test_layout.addWidget(progress)
        test_dialog.setLayout(test_layout)

        test_dialog.show()
        QApplication.processEvents()

        try:
            client = WAPIClient(instance_id, token)
            dados = client.buscar_chats(per_page=1)

            test_dialog.close()

            if dados:
                QMessageBox.information(
                    self,
                    "✅ Sucesso",
                    f"Conexão estabelecida!\n\nTotal de chats: {dados.get('totalChats', 'N/A')}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "⚠️ Aviso",
                    "Conexão estabelecida, mas nenhum dado retornado.\nVerifique as credenciais."
                )
        except Exception as e:
            test_dialog.close()
            QMessageBox.critical(
                self,
                "❌ Erro",
                f"Erro na conexão:\n\n{str(e)}"
            )

    def get_configuracao(self):
        """Retorna as configurações inseridas"""
        return {
            'instance_id': self.instance_id_input.text().strip(),
            'token': self.token_input.text().strip(),
            'webhook_id': self.webhook_id_input.text().strip(),
            'intervalo_webhook': int(self.intervalo_input.currentText().split()[0]),
            'max_conversas': int(self.max_conversas_input.currentText())
        }


class MainWindow(QMainWindow):
    """Janela principal da aplicação"""

    def __init__(self):
        super().__init__()
        # Configurações padrão
        self.configuracao = {
            'instance_id': '3B6XIW-ZTS923-GEAY6V',
            'token': 'Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF',
            'webhook_id': '0e6e92fd-c357-44e4-b1e5-067d6ae4cd0d',
            'intervalo_webhook': 3,
            'max_conversas': 50
        }

        self.wapi_client = None
        self.webhook_monitor = None

        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.inicializar_servicos()

    def setup_ui(self):
        self.setWindowTitle("WhatsApp Business - Atendimento Comercial")
        self.setGeometry(100, 100, 1200, 800)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Splitter para dividir a tela
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Painel esquerdo - Lista de conversas
        painel_esquerdo = QWidget()
        painel_esquerdo.setMaximumWidth(400)
        painel_esquerdo.setMinimumWidth(300)
        painel_esquerdo.setStyleSheet("background-color: white; border-right: 1px solid #E0E0E0;")

        layout_esquerdo = QVBoxLayout()
        layout_esquerdo.setContentsMargins(0, 0, 0, 0)
        layout_esquerdo.setSpacing(0)

        # Header do painel esquerdo
        header_esquerdo = QFrame()
        header_esquerdo.setFixedHeight(70)
        header_esquerdo.setStyleSheet("background-color: #F0F2F5; border-bottom: 1px solid #E0E0E0;")

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 0, 20, 0)

        titulo_app = QLabel("Conversas")
        titulo_app.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

        # Botão de atualizar conversas
        btn_atualizar = QPushButton("🔄")
        btn_atualizar.setToolTip("Atualizar conversas")
        btn_atualizar.clicked.connect(self.atualizar_conversas)
        btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #20BD5F;
            }
        """)

        # Indicador de status do webhook
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #FF0000; font-size: 20px;")
        self.status_indicator.setToolTip("Status do Webhook")

        header_layout.addWidget(titulo_app)
        header_layout.addStretch()
        header_layout.addWidget(self.status_indicator)
        header_layout.addWidget(btn_atualizar)
        header_esquerdo.setLayout(header_layout)

        # Lista de conversas
        self.lista_conversas = ListaConversas()

        layout_esquerdo.addWidget(header_esquerdo)
        layout_esquerdo.addWidget(self.lista_conversas, 1)
        painel_esquerdo.setLayout(layout_esquerdo)

        # Painel direito - Área de chat
        self.area_chat = AreaChat()

        splitter.addWidget(painel_esquerdo)
        splitter.addWidget(self.area_chat)

        # Definir proporções
        splitter.setSizes([350, 850])

        layout.addWidget(splitter)
        central_widget.setLayout(layout)

        # Conectar sinais
        self.lista_conversas.conversa_selecionada.connect(self.area_chat.carregar_conversa)

    def setup_menu(self):
        """Configura a barra de menu"""
        menubar = self.menuBar()

        # Menu Arquivo
        menu_arquivo = menubar.addMenu("Arquivo")

        action_atualizar = QAction("Atualizar Conversas", self)
        action_atualizar.setShortcut("F5")
        action_atualizar.triggered.connect(self.atualizar_conversas)
        menu_arquivo.addAction(action_atualizar)

        menu_arquivo.addSeparator()

        action_sair = QAction("Sair", self)
        action_sair.setShortcut("Ctrl+Q")
        action_sair.triggered.connect(self.close)
        menu_arquivo.addAction(action_sair)

        # Menu Configurações
        menu_config = menubar.addMenu("Configurações")

        action_configurar = QAction("Configurar APIs", self)
        action_configurar.triggered.connect(self.abrir_configuracoes)
        menu_config.addAction(action_configurar)

        action_webhook = QAction("Reiniciar Webhook", self)
        action_webhook.triggered.connect(self.reiniciar_webhook)
        menu_config.addAction(action_webhook)

        menu_config.addSeparator()

        action_sobre = QAction("Sobre", self)
        action_sobre.triggered.connect(self.mostrar_sobre)
        menu_config.addAction(action_sobre)

    def setup_status_bar(self):
        """Configura a barra de status"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status da conexão W-API
        self.status_wapi = QLabel("W-API: Desconectado")
        self.status_wapi.setStyleSheet("color: #FF0000; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.status_wapi)

        # Status do Webhook
        self.status_webhook = QLabel("Webhook: Desconectado")
        self.status_webhook.setStyleSheet("color: #FF0000; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.status_webhook)

        self.status_bar.showMessage("Inicializando...")

    def inicializar_servicos(self):
        """Inicializa os serviços W-API e Webhook"""
        # Inicializar W-API
        self.wapi_client = WAPIClient(
            self.configuracao['instance_id'],
            self.configuracao['token']
        )

        # Testar conexão W-API
        self.testar_wapi()

        # Atualizar lista de conversas na interface
        self.lista_conversas.wapi_client = self.wapi_client
        self.area_chat.wapi_client = self.wapi_client

        # Inicializar Webhook Monitor
        self.iniciar_webhook()

        # Carregar conversas iniciais
        self.atualizar_conversas()

    def testar_wapi(self):
        """Testa conexão com W-API"""
        try:
            dados = self.wapi_client.buscar_chats(per_page=1)
            if dados:
                self.status_wapi.setText("W-API: Conectado")
                self.status_wapi.setStyleSheet("color: #25D366; font-weight: bold;")
                return True
            else:
                self.status_wapi.setText("W-API: Erro")
                self.status_wapi.setStyleSheet("color: #FF0000; font-weight: bold;")
                return False
        except Exception as e:
            self.status_wapi.setText(f"W-API: Erro - {str(e)[:20]}")
            self.status_wapi.setStyleSheet("color: #FF0000; font-weight: bold;")
            return False

    def iniciar_webhook(self):
        """Inicia o monitor de webhook"""
        if self.webhook_monitor:
            self.webhook_monitor.stop()
            self.webhook_monitor.wait()

        self.webhook_monitor = WebhookMonitor(self.configuracao['webhook_id'])
        self.webhook_monitor.nova_mensagem.connect(self.processar_nova_mensagem)
        self.webhook_monitor.status_changed.connect(self.atualizar_status_webhook)
        self.webhook_monitor.start()

    def reiniciar_webhook(self):
        """Reinicia o monitor de webhook"""
        self.status_bar.showMessage("Reiniciando webhook...")
        self.iniciar_webhook()

    def processar_nova_mensagem(self, data):
        """Processa nova mensagem recebida do webhook"""
        try:
            # Processar na área de chat se for da conversa atual
            self.area_chat.processar_mensagem_webhook(data)

            # Atualizar lista de conversas
            chat = data.get('chat', {})
            chat_id = chat.get('id', '')
            if chat_id:
                self.lista_conversas.atualizar_conversa(chat_id, data)

            # Notificação na status bar
            sender = data.get('sender', {})
            sender_name = sender.get('pushName', 'Contato')
            self.status_bar.showMessage(f"Nova mensagem de {sender_name}", 3000)

        except Exception as e:
            print(f"Erro ao processar nova mensagem: {e}")

    def atualizar_status_webhook(self, status):
        """Atualiza o status do webhook na interface"""
        if "Conectado" in status:
            self.status_webhook.setText("Webhook: Conectado")
            self.status_webhook.setStyleSheet("color: #25D366; font-weight: bold;")
            self.status_indicator.setStyleSheet("color: #25D366; font-size: 20px;")
            self.status_indicator.setToolTip("Webhook conectado")
        else:
            self.status_webhook.setText(f"Webhook: {status}")
            self.status_webhook.setStyleSheet("color: #FF0000; font-weight: bold;")
            self.status_indicator.setStyleSheet("color: #FF0000; font-size: 20px;")
            self.status_indicator.setToolTip(f"Webhook: {status}")

    def atualizar_conversas(self):
        """Atualiza a lista de conversas"""
        self.status_bar.showMessage("Atualizando conversas...")
        self.lista_conversas.carregar_chats()
        self.status_bar.showMessage("Conversas atualizadas", 2000)

    def abrir_configuracoes(self):
        """Abre o dialog de configurações"""
        dialog = ConfiguracaoDialog(self)

        # Pré-preencher com configurações atuais
        dialog.instance_id_input.setText(self.configuracao['instance_id'])
        dialog.token_input.setText(self.configuracao['token'])
        dialog.webhook_id_input.setText(self.configuracao['webhook_id'])
        dialog.intervalo_input.setCurrentText(f"{self.configuracao['intervalo_webhook']} segundos")
        dialog.max_conversas_input.setCurrentText(str(self.configuracao['max_conversas']))

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Salvar novas configurações
            self.configuracao = dialog.get_configuracao()

            # Reinicializar serviços
            self.status_bar.showMessage("Aplicando configurações...")
            self.inicializar_servicos()
            self.status_bar.showMessage("Configurações aplicadas!", 2000)

    def mostrar_sobre(self):
        """Mostra informações sobre o aplicativo"""
        QMessageBox.about(self, "Sobre",
                          "WhatsApp Business - Atendimento Comercial\n\n"
                          "Sistema integrado com:\n"
                          "• W-API para envio e recebimento\n"
                          "• Webhook para mensagens em tempo real\n"
                          "• Interface moderna similar ao WhatsApp\n\n"
                          "Desenvolvido com PyQt6\n"
                          "Versão 2.0 - Integrado")

    def closeEvent(self, event):
        """Evento de fechamento da aplicação"""
        if self.webhook_monitor:
            self.webhook_monitor.stop()
            self.webhook_monitor.wait()
        event.accept()


def main():
    """Função principal"""
    app = QApplication(sys.argv)

    # Configurar estilo da aplicação
    app.setStyle('Fusion')

    # Paleta de cores
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 242, 245))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    app.setPalette(palette)

    # Criar e mostrar janela principal
    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 Aplicação encerrada!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")


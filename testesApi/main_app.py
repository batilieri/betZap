#!/usr/bin/env python3
"""
Interface de Atendimento Comercial - WhatsApp Business
Interface similar ao WhatsApp para atendimento comercial
"""

import sys
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QPushButton,
    QLabel, QFrame, QScrollArea, QSplitter, QHeaderView, QToolBar,
    QStatusBar, QMessageBox, QDialog, QFormLayout, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import (
    QFont, QPalette, QColor, QPixmap, QIcon, QAction,
    QPainter, QPen, QBrush
)


class ConversaItem(QWidget):
    """Widget personalizado para item da lista de conversas"""

    def __init__(self, nome, ultima_mensagem, horario, telefone, nao_lidas=0):
        super().__init__()
        self.nome = nome
        self.telefone = telefone
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

    def __init__(self, texto, enviada_por_mim=False, horario="", tipo_midia=None):
        super().__init__()
        self.enviada_por_mim = enviada_por_mim
        self.setup_ui(texto, horario, tipo_midia)

    def setup_ui(self, texto, horario, tipo_midia):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        # Container da mensagem
        container = QFrame()
        container.setMaximumWidth(400)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(12, 8, 12, 8)
        container_layout.setSpacing(4)

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

    def __init__(self):
        super().__init__()
        self.conversa_atual = None
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

    def carregar_conversa(self, nome, telefone):
        """Carrega uma conversa específica"""
        self.conversa_atual = {"nome": nome, "telefone": telefone}

        # Atualizar header
        self.nome_contato.setText(nome)
        self.status_contato.setText(telefone)
        self.avatar_contato.setText(nome[0].upper() if nome else "?")

        # Limpar mensagens anteriores
        self.limpar_mensagens()

        # Carregar mensagens da conversa
        self.carregar_mensagens_exemplo()

    def limpar_mensagens(self):
        """Remove todas as mensagens da área de chat"""
        while self.mensagens_layout.count():
            child = self.mensagens_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def carregar_mensagens_exemplo(self):
        """Carrega mensagens de exemplo"""
        if not self.conversa_atual:
            return

        # Mensagens de exemplo baseadas nos dados fornecidos
        mensagens_exemplo = [
            {"texto": "Oi, tudo bem?", "enviada_por_mim": False, "horario": "10:30"},
            {"texto": "Oi! Tudo ótimo, obrigado!", "enviada_por_mim": True, "horario": "10:32"},
            {"texto": "Gostaria de saber mais sobre seus produtos", "enviada_por_mim": False, "horario": "10:33"},
            {"texto": "", "enviada_por_mim": False, "horario": "10:35", "tipo_midia": "image"},
            {"texto": "Claro! Temos várias opções disponíveis. Que tipo de produto você procura?",
             "enviada_por_mim": True, "horario": "10:36"},
        ]

        for msg in mensagens_exemplo:
            self.adicionar_mensagem(
                msg["texto"],
                msg["enviada_por_mim"],
                msg["horario"],
                msg.get("tipo_midia")
            )

    def adicionar_mensagem(self, texto, enviada_por_mim=True, horario="", tipo_midia=None):
        """Adiciona uma nova mensagem ao chat"""
        if not horario:
            horario = datetime.now().strftime("%H:%M")

        mensagem = MensagemWidget(texto, enviada_por_mim, horario, tipo_midia)
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
        if not texto:
            return

        # Adicionar mensagem enviada
        self.adicionar_mensagem(texto, True)

        # Limpar input
        self.input_mensagem.clear()

        # Simular resposta automática (apenas para demonstração)
        QTimer.singleShot(1000, lambda: self.adicionar_mensagem(
            "Mensagem recebida! Em breve retornamos o contato.", False
        ))


class ListaConversas(QListWidget):
    """Lista de conversas personalizada"""

    conversa_selecionada = pyqtSignal(str, str)  # nome, telefone

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.carregar_conversas_exemplo()

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

    def carregar_conversas_exemplo(self):
        """Carrega conversas de exemplo baseadas nos dados fornecidos"""
        conversas = [
            {"nome": "𝓣𝓱𝓪𝔂𝓷𝓪🍃", "telefone": "556999267344", "ultima_msg": "Caracas isso é muit9 bom",
             "horario": "00:03", "nao_lidas": 2},
            {"nome": "João Silva", "telefone": "5511987654321", "ultima_msg": "Obrigado pelo atendimento!",
             "horario": "23:45", "nao_lidas": 0},
            {"nome": "Maria Santos", "telefone": "5511876543210", "ultima_msg": "Quando vocês abrem amanhã?",
             "horario": "22:30", "nao_lidas": 1},
            {"nome": "Pedro Costa", "telefone": "5511765432109", "ultima_msg": "Perfeito, vou passar aí",
             "horario": "21:15", "nao_lidas": 0},
            {"nome": "Ana Oliveira", "telefone": "5511654321098", "ultima_msg": "Vocês fazem entrega?",
             "horario": "20:45", "nao_lidas": 3},
        ]

        for conversa in conversas:
            self.adicionar_conversa(
                conversa["nome"],
                conversa["telefone"],
                conversa["ultima_msg"],
                conversa["horario"],
                conversa["nao_lidas"]
            )

    def adicionar_conversa(self, nome, telefone, ultima_msg, horario, nao_lidas=0):
        """Adiciona uma nova conversa à lista"""
        item = QListWidgetItem()
        widget = ConversaItem(nome, ultima_msg, horario, telefone, nao_lidas)

        item.setSizeHint(widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, widget)

    def on_conversa_clicada(self, item):
        """Callback quando uma conversa é clicada"""
        widget = self.itemWidget(item)
        if widget:
            self.conversa_selecionada.emit(widget.nome, widget.telefone)


class MainWindow(QMainWindow):
    """Janela principal da aplicação"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()

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

        # Botão de nova conversa
        btn_nova_conversa = QPushButton("+ Nova")
        btn_nova_conversa.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #20BD5F;
            }
        """)

        header_layout.addWidget(titulo_app)
        header_layout.addStretch()
        header_layout.addWidget(btn_nova_conversa)
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

        action_nova_conversa = QAction("Nova Conversa", self)
        action_nova_conversa.setShortcut("Ctrl+N")
        menu_arquivo.addAction(action_nova_conversa)

        menu_arquivo.addSeparator()

        action_sair = QAction("Sair", self)
        action_sair.setShortcut("Ctrl+Q")
        action_sair.triggered.connect(self.close)
        menu_arquivo.addAction(action_sair)

        # Menu Configurações
        menu_config = menubar.addMenu("Configurações")

        action_webhook = QAction("Configurar Webhook", self)
        menu_config.addAction(action_webhook)

        action_sobre = QAction("Sobre", self)
        action_sobre.triggered.connect(self.mostrar_sobre)
        menu_config.addAction(action_sobre)

    def setup_status_bar(self):
        """Configura a barra de status"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status da conexão
        self.status_conexao = QLabel("● Conectado")
        self.status_conexao.setStyleSheet("color: #25D366; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.status_conexao)

        self.status_bar.showMessage("Pronto para atendimento")

    def mostrar_sobre(self):
        """Mostra informações sobre o aplicativo"""
        QMessageBox.about(self, "Sobre",
                          "WhatsApp Business - Atendimento Comercial\n\n"
                          "Interface para atendimento comercial integrada com W-API\n"
                          "Desenvolvido com PyQt6\n\n"
                          "Versão 1.0")


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
    sys.exit(main())
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget de mensagens fofas SUAVIZADO - Interface limpa sem popups
Remoção de tooltips e janelas flutuantes para experiência mais suave
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QPushButton, QScrollArea,
    QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath, QPixmap
from datetime import datetime
from typing import Dict


class MessageBubble(QFrame):
    """Balão de mensagem fofo com design arredondado - VERSÃO SUAVIZADA"""

    def __init__(self, message_data: Dict, is_from_me: bool = False):
        super().__init__()
        self.message_data = message_data
        self.is_from_me = is_from_me
        self.is_fully_setup = False
        self.setup_ui()
        self.setup_animation()

    def setup_ui(self):
        """Configura a interface do balão - SUAVIZADO"""
        # Configurações básicas do widget
        self.setMaximumWidth(500)
        self.setMinimumHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 8, 5, 8)
        main_layout.setSpacing(3)

        # Nome do remetente (apenas para mensagens recebidas em grupos)
        if not self.is_from_me and self.message_data.get('is_group', False):
            sender_name = self.message_data.get('sender_name', 'Desconhecido')
            if sender_name != 'Você':  # Não mostrar "Você" em grupos
                sender_label = QLabel(sender_name)
                sender_label.setFont(QFont('Segoe UI', 9, QFont.Weight.Bold))
                sender_label.setStyleSheet("color: #667eea; margin-left: 15px; margin-bottom: 2px;")
                main_layout.addWidget(sender_label)

        # Container do balão
        bubble_container = QHBoxLayout()
        bubble_container.setContentsMargins(0, 0, 0, 0)
        bubble_container.setSpacing(0)

        # Criar o balão da mensagem
        self.bubble_frame = self._create_bubble()

        # Alinhar balão baseado no remetente
        if self.is_from_me:
            # Mensagens enviadas - lado direito
            bubble_container.addStretch(1)
            bubble_container.addWidget(self.bubble_frame, 0)
        else:
            # Mensagens recebidas - lado esquerdo
            bubble_container.addWidget(self.bubble_frame, 0)
            bubble_container.addStretch(1)

        main_layout.addLayout(bubble_container)

        # Configurar o layout principal
        self.setLayout(main_layout)

        # Estilo do container principal - SEM HOVER OU FOCUS
        self.setStyleSheet("""
            MessageBubble { 
                background-color: transparent; 
                border: none; 
            }
            MessageBubble:hover { 
                background-color: transparent; 
            }
        """)

        # Garantir visibilidade
        self.setVisible(True)
        self.is_fully_setup = True

    def _create_bubble(self) -> QFrame:
        """Cria o balão da mensagem - VERSÃO SUAVIZADA"""
        bubble = QFrame()
        bubble.setMaximumWidth(400)
        bubble.setMinimumWidth(120)
        bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # Layout do balão
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(15, 12, 15, 12)
        bubble_layout.setSpacing(5)

        # Ícone baseado no tipo da mensagem
        message_type = self.message_data.get('message_type', 'text')
        type_icon = self._get_type_icon(message_type)

        # Conteúdo principal
        content_text = f"{type_icon}{self.message_data.get('content', '')}"

        content_label = QLabel(content_text)
        content_label.setWordWrap(True)
        content_label.setFont(QFont('Segoe UI', 11))
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # Cor do texto baseada no tema
        text_color = "#ffffff" if self.is_from_me else "#2c3e50"
        content_label.setStyleSheet(f"""
            color: {text_color}; 
            background: transparent; 
            border: none;
            selection-background-color: rgba(255, 255, 255, 0.3);
        """)

        bubble_layout.addWidget(content_label)

        # Adicionar informações extras baseadas no tipo
        if message_type != 'text':
            extra_widget = self._create_media_preview()
            if extra_widget:
                bubble_layout.addWidget(extra_widget)

        # Horário da mensagem
        timestamp_str = self.message_data.get('timestamp_str', '')
        if timestamp_str:
            time_label = QLabel(timestamp_str)
            time_label.setFont(QFont('Segoe UI', 8))
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

            time_color = "rgba(255,255,255,0.8)" if self.is_from_me else "#7f8c8d"
            time_label.setStyleSheet(f"color: {time_color}; background: transparent; margin-top: 3px;")

            bubble_layout.addWidget(time_label)

        # Aplicar estilo visual ao balão
        self._apply_bubble_style(bubble)

        # Adicionar sombra suave
        self._add_shadow(bubble)

        return bubble

    def _apply_bubble_style(self, bubble: QFrame):
        """Aplica estilo visual ao balão - SEM EFEITOS DE HOVER"""
        if self.is_from_me:
            # Mensagens enviadas - gradiente azul/roxo
            bubble.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    border-radius: 18px;
                    border-bottom-right-radius: 5px;
                }
            """)
        else:
            # Mensagens recebidas - branco com borda suave
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #e9ecef;
                    border-radius: 18px;
                    border-bottom-left-radius: 5px;
                }
            """)

    def _add_shadow(self, bubble: QFrame):
        """Adiciona sombra mais suave ao balão"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)  # Reduzido para ser mais sutil
        shadow.setColor(QColor(0, 0, 0, 20))  # Mais transparente
        shadow.setOffset(0, 2)  # Menos offset
        bubble.setGraphicsEffect(shadow)

    def _get_type_icon(self, message_type: str) -> str:
        """Retorna ícone baseado no tipo da mensagem"""
        icons = {
            'text': '',
            'sticker': '🏷️ ',
            'image': '📷 ',
            'video': '🎥 ',
            'audio': '🎵 ',
            'document': '📄 ',
            'location': '📍 ',
            'poll': '📊 ',
            'unknown': '📱 '
        }
        return icons.get(message_type, '📱 ')

    def _create_media_preview(self) -> QWidget:
        """Cria preview para mensagens de mídia - SUAVIZADO"""
        message_type = self.message_data.get('message_type', 'text')
        media_data = self.message_data.get('media_data', {})

        if not media_data:
            return None

        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 5, 0, 0)
        preview_layout.setSpacing(3)

        if message_type == 'document':
            # Preview de documento
            filename = media_data.get('filename', 'documento')
            file_size = media_data.get('file_length', 0)

            if file_size:
                try:
                    size_mb = round(int(file_size) / (1024 * 1024), 2)
                    size_str = f" ({size_mb} MB)" if size_mb > 0 else ""
                except:
                    size_str = ""
            else:
                size_str = ""

            doc_label = QLabel(f"📎 {filename}{size_str}")
            doc_label.setFont(QFont('Segoe UI', 9))
            doc_label.setStyleSheet("color: #667eea; font-style: italic;")
            preview_layout.addWidget(doc_label)

        elif message_type == 'location':
            # Preview de localização
            location_name = media_data.get('name', '')
            address = media_data.get('address', '')

            if location_name:
                loc_label = QLabel(f"🗺️ {location_name}")
            else:
                loc_label = QLabel("🗺️ Localização compartilhada")

            loc_label.setFont(QFont('Segoe UI', 9))
            loc_label.setStyleSheet("color: #27ae60; font-style: italic;")
            preview_layout.addWidget(loc_label)

            if address:
                addr_label = QLabel(address)
                addr_label.setFont(QFont('Segoe UI', 8))
                addr_label.setStyleSheet("color: #7f8c8d;")
                addr_label.setWordWrap(True)
                preview_layout.addWidget(addr_label)

        elif message_type == 'poll':
            # Preview de enquete
            poll_name = media_data.get('name', 'Enquete')
            options = media_data.get('options', [])

            poll_label = QLabel(f"🗳️ {poll_name}")
            poll_label.setFont(QFont('Segoe UI', 9, QFont.Weight.Bold))
            poll_label.setStyleSheet("color: #e67e22;")
            preview_layout.addWidget(poll_label)

            # Mostrar algumas opções
            for i, option in enumerate(options[:3]):
                option_label = QLabel(f"• {option}")
                option_label.setFont(QFont('Segoe UI', 8))
                option_label.setStyleSheet("color: #95a5a6; margin-left: 10px;")
                preview_layout.addWidget(option_label)

            if len(options) > 3:
                more_label = QLabel(f"... e mais {len(options) - 3} opções")
                more_label.setFont(QFont('Segoe UI', 8))
                more_label.setStyleSheet("color: #bdc3c7; font-style: italic; margin-left: 10px;")
                preview_layout.addWidget(more_label)

        elif message_type in ['image', 'video']:
            # Preview de mídia visual
            media_label = QLabel("🖼️ Mídia anexada" if message_type == 'image' else "🎬 Vídeo anexado")
            media_label.setFont(QFont('Segoe UI', 9))
            media_label.setStyleSheet("color: #3498db; font-style: italic;")
            preview_layout.addWidget(media_label)

        return preview_widget

    def setup_animation(self):
        """Configura animação de entrada mais suave"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)  # Mais rápida
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuart)  # Mais suave

    def animate_in(self):
        """Anima a entrada do balão suavemente"""
        if not self.is_fully_setup:
            return

        # Geometria inicial (altura 0)
        start_rect = self.geometry()
        start_rect.setHeight(0)

        # Geometria final (altura normal)
        end_rect = self.geometry()

        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()

    def sizeHint(self):
        """Retorna tamanho sugerido do widget"""
        if hasattr(self, 'bubble_frame') and self.bubble_frame:
            bubble_size = self.bubble_frame.sizeHint()
            return bubble_size
        return super().sizeHint()


class DateSeparator(QWidget):
    """Separador de data suave entre mensagens"""

    def __init__(self, date_str: str):
        super().__init__()
        self.date_str = date_str
        self.setup_ui()

    def setup_ui(self):
        """Configura o separador de data - VERSÃO SUAVIZADA"""
        self.setFixedHeight(45)  # Ligeiramente menor
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)

        # Linha esquerda
        left_line = QFrame()
        left_line.setFrameStyle(QFrame.Shape.HLine)
        left_line.setStyleSheet("border: 1px solid #e3e6ea;")  # Cor mais suave

        # Label da data
        date_label = QLabel(self.date_str)
        date_label.setFont(QFont('Segoe UI', 9, QFont.Weight.Bold))
        date_label.setStyleSheet("""
            QLabel {
                background-color: #fafbfc;
                color: #6c757d;
                padding: 5px 14px;
                border-radius: 12px;
                border: 1px solid #e3e6ea;
            }
        """)
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Linha direita
        right_line = QFrame()
        right_line.setFrameStyle(QFrame.Shape.HLine)
        right_line.setStyleSheet("border: 1px solid #e3e6ea;")

        layout.addWidget(left_line, 1)
        layout.addWidget(date_label, 0)
        layout.addWidget(right_line, 1)


class ChatHeader(QWidget):
    """Cabeçalho do chat com informações do contato/grupo - SUAVIZADO"""

    info_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Configura o cabeçalho - SEM TOOLTIPS"""
        self.setFixedHeight(75)  # Ligeiramente menor
        self.setStyleSheet("""
            ChatHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(15)

        # Avatar
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(45, 45)  # Ligeiramente menor
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                color: #667eea;
                border-radius: 22px;
                font-weight: bold;
                font-size: 16px;
            }
        """)

        # Informações do chat
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.chat_name = QLabel("")
        self.chat_name.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))  # Ligeiramente menor
        self.chat_name.setStyleSheet("color: white; margin: 0;")

        self.chat_status = QLabel("")
        self.chat_status.setFont(QFont('Segoe UI', 9))
        self.chat_status.setStyleSheet("color: #ecf0f1; margin: 0;")

        info_layout.addWidget(self.chat_name)
        info_layout.addWidget(self.chat_status)

        # Botões de ação - SEM TOOLTIPS
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        self.info_btn = QPushButton("ℹ️")
        self.info_btn.setFixedSize(36, 36)  # Ligeiramente menor
        self.info_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                border: none;
                border-radius: 18px;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.35);
            }
        """)
        # REMOVIDO: setToolTip para evitar popups
        self.info_btn.clicked.connect(self.info_clicked.emit)

        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(36, 36)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                border: none;
                border-radius: 18px;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.35);
            }
        """)
        # REMOVIDO: setToolTip para evitar popups

        actions_layout.addWidget(self.info_btn)
        actions_layout.addWidget(self.refresh_btn)

        # Montar layout
        layout.addWidget(self.avatar_label)
        layout.addLayout(info_layout, 1)
        layout.addLayout(actions_layout)

    def update_chat_info(self, chat_data: Dict):
        """Atualiza informações do chat no cabeçalho"""
        chat_name = chat_data.get('chat_name', 'Chat')
        chat_type = chat_data.get('chat_type', 'individual')
        total_messages = chat_data.get('total_messages', 0)
        participants_count = chat_data.get('participants_count', 0)

        # Atualizar nome
        self.chat_name.setText(chat_name)

        # Atualizar avatar
        initial = chat_name[0].upper() if chat_name else '?'
        self.avatar_label.setText(initial)

        # Atualizar status
        if chat_type == 'group':
            status_text = f"Grupo • {participants_count} participantes • {total_messages} mensagens"
        else:
            status_text = f"Contato • {total_messages} mensagens"

        self.chat_status.setText(status_text)


class MessagesContainer(QScrollArea):
    """Container otimizado para mensagens - VERSÃO SUAVIZADA"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Configura o container de mensagens - MAIS SUAVE"""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f9fa;
            }
            QScrollBar:vertical {
                background: #f1f3f4;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #dadce0;
                border-radius: 4px;
                min-height: 25px;
            }
            QScrollBar::handle:vertical:hover {
                background: #bdc1c6;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        # Widget interno para as mensagens
        self.messages_widget = QWidget()
        self.messages_widget.setStyleSheet("background-color: transparent;")

        # Layout para as mensagens
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(8, 8, 8, 8)  # Margens menores
        self.messages_layout.setSpacing(3)  # Espaçamento menor
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Definir o widget interno
        self.setWidget(self.messages_widget)

    def add_message_widget(self, widget):
        """Adiciona um widget de mensagem ao container - SUAVIZADO"""
        # Garantir que o widget seja visível
        widget.setVisible(True)

        # Adicionar ao layout
        self.messages_layout.addWidget(widget)

        # Atualizar geometria suavemente
        self.messages_widget.updateGeometry()

        # Processar eventos de forma não bloqueante
        QApplication.processEvents()

        # Rolar para o final com delay menor
        QTimer.singleShot(50, self.scroll_to_bottom_smooth)

    def clear_messages(self):
        """Limpa todas as mensagens"""
        while self.messages_layout.count() > 0:
            child = self.messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Processar eventos para garantir limpeza
        QApplication.processEvents()

    def scroll_to_bottom_smooth(self):
        """Rola suavemente para o final das mensagens"""
        scrollbar = self.verticalScrollBar()

        # Animação suave do scroll
        current_value = scrollbar.value()
        target_value = scrollbar.maximum()

        if abs(target_value - current_value) > 10:
            # Se a distância for grande, animar
            self.scroll_animation = QPropertyAnimation(scrollbar, b"value")
            self.scroll_animation.setDuration(200)
            self.scroll_animation.setStartValue(current_value)
            self.scroll_animation.setEndValue(target_value)
            self.scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.scroll_animation.start()
        else:
            # Se for pequena, ir direto
            scrollbar.setValue(target_value)

    def scroll_to_bottom(self):
        """Rola para o final das mensagens (versão rápida)"""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def add_stretch(self):
        """Adiciona stretch no final para empurrar mensagens para cima"""
        self.messages_layout.addStretch()


class MessageRenderer:
    """Renderizador de mensagens para o chat - VERSÃO SUAVIZADA"""

    @staticmethod
    def create_message_widget(message_data: Dict) -> QWidget:
        """
        Cria widget de mensagem baseado nos dados

        Args:
            message_data: Dados da mensagem do banco

        Returns:
            Widget da mensagem renderizada
        """
        from_me = message_data.get('from_me', False)

        # Criar balão da mensagem
        message_bubble = MessageBubble(message_data, is_from_me=from_me)

        return message_bubble

    @staticmethod
    def create_date_separator(date_str: str) -> QWidget:
        """Cria separador de data"""
        return DateSeparator(date_str)

    @staticmethod
    def should_show_date_separator(current_msg: Dict, previous_msg: Dict = None) -> bool:
        """
        Verifica se deve mostrar separador de data entre mensagens

        Args:
            current_msg: Mensagem atual
            previous_msg: Mensagem anterior (pode ser None)

        Returns:
            True se deve mostrar separador
        """
        if not previous_msg:
            return True

        current_date = current_msg.get('date_str', '')
        previous_date = previous_msg.get('date_str', '')

        return current_date != previous_date

    @staticmethod
    def format_date_separator(date_str: str) -> str:
        """
        Formata string de data para o separador

        Args:
            date_str: Data no formato 'DD/MM/YYYY'

        Returns:
            Data formatada para exibição
        """
        try:
            # Tentar parsear e reformatar
            from datetime import datetime
            dt = datetime.strptime(date_str, '%d/%m/%Y')

            # Verificar se é hoje, ontem, etc.
            today = datetime.now()
            if dt.date() == today.date():
                return "Hoje"
            elif (today.date() - dt.date()).days == 1:
                return "Ontem"
            elif (today.date() - dt.date()).days < 7:
                dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                return dias_semana[dt.weekday()]
            else:
                return dt.strftime('%d de %B')
        except:
            return date_str

    @staticmethod
    def create_chat_header() -> ChatHeader:
        """Cria cabeçalho do chat"""
        return ChatHeader()

    @staticmethod
    def create_messages_container() -> MessagesContainer:
        """Cria container de mensagens"""
        return MessagesContainer()


# Exemplo de uso para testar a suavização
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # Criar container de teste
    container = MessagesContainer()

    # Dados de teste
    test_messages = [
        {
            'content': 'Olá! Como você está?',
            'from_me': False,
            'timestamp_str': '14:30',
            'message_type': 'text',
            'date_str': '07/06/2025'
        },
        {
            'content': 'Estou bem, obrigado! E você?',
            'from_me': True,
            'timestamp_str': '14:32',
            'message_type': 'text',
            'date_str': '07/06/2025'
        },
        {
            'content': 'Também estou bem! Viu as novidades?',
            'from_me': False,
            'timestamp_str': '14:35',
            'message_type': 'text',
            'date_str': '07/06/2025'
        }
    ]

    # Adicionar mensagens de teste
    for msg in test_messages:
        widget = MessageRenderer.create_message_widget(msg)
        container.add_message_widget(widget)

    container.resize(600, 400)
    container.show()

    sys.exit(app.exec())
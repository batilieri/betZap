#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget de entrada aprimorado para envio de mensagens
Suporte a texto, emojis, anexos, gravação de áudio
"""

import os
import sys
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton,
    QTextEdit, QLabel, QFrame, QProgressBar, QFileDialog,
    QMessageBox, QMenu, QAction, QScrollArea, QGridLayout,
    QToolButton, QButtonGroup, QApplication
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QPropertyAnimation, QRect,
    QEasingCurve, QSize, QThread, pyqtSlot
)
from PyQt6.QtGui import (
    QFont, QPixmap, QIcon, QKeySequence, QShortcut,
    QPainter, QPen, QColor, QTextCursor
)
from datetime import datetime


class EmojiPanel(QWidget):
    """Painel de emojis fofo"""

    emoji_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.is_visible = False

    def setup_ui(self):
        """Configura o painel de emojis"""
        self.setFixedSize(320, 240)
        self.setStyleSheet("""
            EmojiPanel {
                background-color: white;
                border: 2px solid #e9ecef;
                border-radius: 15px;
            }
        """)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Título
        title_label = QLabel("😊 Emojis")
        title_label.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #667eea; margin-bottom: 5px;")
        layout.addWidget(title_label)

        # Área de scroll para emojis
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #f1f3f4;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #dadce0;
                border-radius: 4px;
            }
        """)

        # Widget dos emojis
        emoji_widget = QWidget()
        emoji_layout = QGridLayout(emoji_widget)
        emoji_layout.setSpacing(3)

        # Lista de emojis organizados por categoria
        emoji_categories = {
            "Rostos": ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇",
                       "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚",
                       "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🤩"],

            "Gestos": ["👋", "🤚", "🖐", "✋", "🖖", "👌", "🤏", "✌", "🤞", "🤟",
                       "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝", "👍", "👎",
                       "✊", "👊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "🙏", "💪"],

            "Objetos": ["❤", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
                        "❣", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟", "☮",
                        "✝", "☪", "🕉", "☸", "✡", "🔯", "🕎", "☯", "☦", "🛐"],

            "Natureza": ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯",
                         "🦁", "🐮", "🐷", "🐽", "🐸", "🐵", "🙈", "🙉", "🙊", "🐒",
                         "🐔", "🐧", "🐦", "🐤", "🐣", "🐥", "🦆", "🦅", "🦉", "🦇"],

            "Comida": ["🍎", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🍈", "🍒", "🍑",
                       "🥭", "🍍", "🥥", "🥝", "🍅", "🍆", "🥑", "🥦", "🥬", "🥒",
                       "🌶", "🌽", "🥕", "🥔", "🍠", "🥐", "🍞", "🥖", "🥨", "🧀"]
        }

        row = 0
        for category, emojis in emoji_categories.items():
            # Label da categoria
            category_label = QLabel(category)
            category_label.setFont(QFont('Segoe UI', 9, QFont.Weight.Bold))
            category_label.setStyleSheet("color: #6c757d; margin: 5px 0px;")
            emoji_layout.addWidget(category_label, row, 0, 1, 6)
            row += 1

            # Botões dos emojis
            col = 0
            for emoji in emojis:
                emoji_btn = QPushButton(emoji)
                emoji_btn.setFixedSize(35, 35)
                emoji_btn.setStyleSheet("""
                    QPushButton {
                        border: none;
                        border-radius: 8px;
                        font-size: 16px;
                        background-color: transparent;
                    }
                    QPushButton:hover {
                        background-color: #f8f9fa;
                    }
                    QPushButton:pressed {
                        background-color: #e9ecef;
                    }
                """)

                # Conectar clique
                emoji_btn.clicked.connect(lambda checked, e=emoji: self.on_emoji_clicked(e))

                emoji_layout.addWidget(emoji_btn, row, col)
                col += 1

                if col >= 6:  # 6 emojis por linha
                    col = 0
                    row += 1

            row += 1  # Espaço entre categorias

        scroll_area.setWidget(emoji_widget)
        layout.addWidget(scroll_area)

    def on_emoji_clicked(self, emoji: str):
        """Emite sinal quando emoji é clicado"""
        self.emoji_selected.emit(emoji)

    def show_animated(self):
        """Mostra o painel com animação"""
        if self.is_visible:
            return

        self.show()
        self.is_visible = True

        # Animação de entrada
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Começar menor e crescer
        start_rect = self.geometry()
        start_rect.setHeight(0)
        end_rect = self.geometry()

        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()

    def hide_animated(self):
        """Esconde o painel com animação"""
        if not self.is_visible:
            return

        self.is_visible = False

        # Animação de saída
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.InCubic)

        start_rect = self.geometry()
        end_rect = self.geometry()
        end_rect.setHeight(0)

        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.finished.connect(self.hide)
        self.animation.start()


class AudioRecorder(QThread):
    """Thread para gravação de áudio"""

    recording_started = pyqtSignal()
    recording_finished = pyqtSignal(str)  # Caminho do arquivo
    recording_error = pyqtSignal(str)
    audio_level = pyqtSignal(int)  # Nível do áudio (0-100)

    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.output_path = ""
        self._stop_requested = False

    def start_recording(self, output_path: str):
        """Inicia gravação"""
        self.output_path = output_path
        self.is_recording = True
        self._stop_requested = False
        self.start()

    def stop_recording(self):
        """Para gravação"""
        self._stop_requested = True
        self.is_recording = False

    def run(self):
        """Thread de gravação"""
        try:
            # TODO: Implementar gravação real com pyaudio ou outro
            # Por enquanto, simular gravação
            import time

            self.recording_started.emit()

            start_time = time.time()
            while not self._stop_requested and (time.time() - start_time) < 60:  # Max 60s
                time.sleep(0.1)

                # Simular nível de áudio
                import random
                level = random.randint(20, 80)
                self.audio_level.emit(level)

            if not self._stop_requested:
                # Criar arquivo de áudio simulado
                with open(self.output_path, 'w') as f:
                    f.write("# Arquivo de áudio simulado")

                self.recording_finished.emit(self.output_path)

        except Exception as e:
            self.recording_error.emit(str(e))


class EnhancedInputWidget(QWidget):
    """Widget de entrada aprimorado para mensagens"""

    # Sinais
    send_text_message = pyqtSignal(str)  # Texto da mensagem
    send_file_message = pyqtSignal(str, str)  # Caminho do arquivo, tipo
    send_audio_message = pyqtSignal(str)  # Caminho do áudio
    send_location_message = pyqtSignal(float, float, str)  # lat, lng, nome

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()

        # Estado
        self.is_recording = False
        self.emoji_panel = None
        self.current_contact = None

        # Recorder
        self.audio_recorder = AudioRecorder()
        self.setup_audio_connections()

    def setup_ui(self):
        """Configura interface aprimorada"""
        self.setFixedHeight(120)
        self.setStyleSheet("""
            EnhancedInputWidget {
                background-color: white;
                border-top: 1px solid #e9ecef;
            }
        """)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(8)

        # Área de progresso (inicialmente oculta)
        self.progress_frame = QFrame()
        self.progress_frame.setFixedHeight(25)
        self.progress_frame.setVisible(False)
        self.progress_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 12px;
                border: 1px solid #e9ecef;
            }
        """)

        progress_layout = QHBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(10, 3, 10, 3)

        self.progress_label = QLabel("Enviando...")
        self.progress_label.setFont(QFont('Segoe UI', 9))
        self.progress_label.setStyleSheet("color: #6c757d;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(15)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 7px;
                background-color: #e9ecef;
                text-align: center;
                font-size: 8px;
                color: #495057;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 7px;
            }
        """)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar, 1)

        main_layout.addWidget(self.progress_frame)

        # Área de entrada principal
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 25px;
            }
            QFrame:focus-within {
                border-color: #667eea;
            }
        """)

        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(5, 5, 5, 5)
        input_layout.setSpacing(5)

        # Botão de anexo
        self.attach_btn = QToolButton()
        self.attach_btn.setFixedSize(40, 40)
        self.attach_btn.setText("📎")
        self.attach_btn.setStyleSheet("""
            QToolButton {
                border: none;
                border-radius: 20px;
                background-color: #e9ecef;
                font-size: 16px;
                color: #6c757d;
            }
            QToolButton:hover {
                background-color: #dee2e6;
            }
            QToolButton:pressed {
                background-color: #ced4da;
            }
        """)
        self.attach_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setup_attach_menu()

        # Campo de texto
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(80)
        self.text_input.setMinimumHeight(40)
        self.text_input.setPlaceholderText("Digite uma mensagem... 😊")
        self.text_input.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: transparent;
                font-size: 14px;
                font-family: 'Segoe UI';
                color: #495057;
                padding: 8px 5px;
            }
            QTextEdit:focus {
                outline: none;
            }
        """)

        # Botão de emoji
        self.emoji_btn = QPushButton("😊")
        self.emoji_btn.setFixedSize(40, 40)
        self.emoji_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 20px;
                background-color: #e9ecef;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
            QPushButton:pressed {
                background-color: #ced4da;
            }
        """)

        # Botão de áudio/envio
        self.action_btn = QPushButton("🎤")
        self.action_btn.setFixedSize(45, 45)
        self.action_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 22px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a6fd8, stop:1 #6a4190);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4e63c6, stop:1 #5e377e);
            }
        """)

        # Layout da entrada
        input_layout.addWidget(self.attach_btn)
        input_layout.addWidget(self.text_input, 1)
        input_layout.addWidget(self.emoji_btn)
        input_layout.addWidget(self.action_btn)

        main_layout.addWidget(input_frame)

        # Painel de emojis (inicialmente oculto)
        self.emoji_panel = EmojiPanel()
        self.emoji_panel.setParent(self)
        self.emoji_panel.hide()

    def setup_attach_menu(self):
        """Configura menu de anexos"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: #f8f9fa;
            }
        """)

        # Ações do menu
        actions = [
            ("📷 Imagem", self.select_image),
            ("📄 Documento", self.select_document),
            ("🎵 Áudio", self.select_audio),
            ("📍 Localização", self.send_location)
        ]

        for text, callback in actions:
            action = QAction(text, self)
            action.triggered.connect(callback)
            menu.addAction(action)

        self.attach_btn.setMenu(menu)

    def setup_connections(self):
        """Conecta sinais"""
        # Texto mudou
        self.text_input.textChanged.connect(self.on_text_changed)

        # Botões
        self.emoji_btn.clicked.connect(self.toggle_emoji_panel)
        self.action_btn.clicked.connect(self.on_action_button_clicked)

        # Enter para enviar
        self.text_input.installEventFilter(self)

    def setup_audio_connections(self):
        """Conecta sinais do gravador"""
        self.audio_recorder.recording_started.connect(self.on_recording_started)
        self.audio_recorder.recording_finished.connect(self.on_recording_finished)
        self.audio_recorder.recording_error.connect(self.on_recording_error)
        self.audio_recorder.audio_level.connect(self.on_audio_level)

    def eventFilter(self, obj, event):
        """Filtra eventos"""
        if obj == self.text_input and event.type() == event.Type.KeyPress:
            # Ctrl+Enter ou Shift+Enter para nova linha
            if event.key() == Qt.Key.Key_Return:
                if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                    self.text_input.insertPlainText('\n')
                    return True
                elif event.modifiers() == Qt.KeyboardModifier.NoModifier:
                    # Enter simples envia mensagem
                    self.send_text_message_signal()
                    return True

        return super().eventFilter(obj, event)

    def on_text_changed(self):
        """Chamado quando texto muda"""
        has_text = bool(self.text_input.toPlainText().strip())

        if has_text:
            self.action_btn.setText("➤")
            self.action_btn.setToolTip("Enviar mensagem (Enter)")
        else:
            self.action_btn.setText("🎤")
            self.action_btn.setToolTip("Gravar áudio")

    def on_action_button_clicked(self):
        """Ação do botão principal"""
        has_text = bool(self.text_input.toPlainText().strip())

        if has_text:
            self.send_text_message_signal()
        else:
            self.toggle_audio_recording()

    def send_text_message_signal(self):
        """Envia mensagem de texto"""
        text = self.text_input.toPlainText().strip()
        if not text:
            return

        if not self.current_contact:
            QMessageBox.warning(self, "Aviso", "Selecione um contato primeiro!")
            return

        # Emitir sinal
        self.send_text_message.emit(text)

        # Limpar campo
        self.text_input.clear()
        self.text_input.setFocus()

    def toggle_audio_recording(self):
        """Alterna gravação de áudio"""
        if not self.is_recording:
            self.start_audio_recording()
        else:
            self.stop_audio_recording()

    def start_audio_recording(self):
        """Inicia gravação de áudio"""
        if not self.current_contact:
            QMessageBox.warning(self, "Aviso", "Selecione um contato primeiro!")
            return

        # Criar diretório temporário
        temp_dir = os.path.join(os.path.expanduser("~"), ".whatsapp_chat", "temp_audio")
        os.makedirs(temp_dir, exist_ok=True)

        # Nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = os.path.join(temp_dir, f"audio_{timestamp}.wav")

        # Iniciar gravação
        self.audio_recorder.start_recording(audio_path)

    def stop_audio_recording(self):
        """Para gravação de áudio"""
        self.audio_recorder.stop_recording()

    @pyqtSlot()
    def on_recording_started(self):
        """Gravação iniciada"""
        self.is_recording = True
        self.action_btn.setText("⏹")
        self.action_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 22px;
                background-color: #dc3545;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)

        # Mostrar progresso
        self.show_progress("Gravando áudio... Clique para parar", 0)

    @pyqtSlot(str)
    def on_recording_finished(self, audio_path: str):
        """Gravação finalizada"""
        self.is_recording = False
        self.hide_progress()

        # Restaurar botão
        self.action_btn.setText("🎤")
        self.action_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 22px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a6fd8, stop:1 #6a4190);
            }
        """)

        # Emitir sinal de áudio
        self.send_audio_message.emit(audio_path)

    @pyqtSlot(str)
    def on_recording_error(self, error: str):
        """Erro na gravação"""
        self.is_recording = False
        self.hide_progress()
        QMessageBox.warning(self, "Erro na Gravação", f"Erro ao gravar áudio:\n{error}")

    @pyqtSlot(int)
    def on_audio_level(self, level: int):
        """Atualiza nível do áudio"""
        if self.is_recording:
            self.update_progress(level)

    def toggle_emoji_panel(self):
        """Mostra/esconde painel de emojis"""
        if self.emoji_panel.is_visible:
            self.emoji_panel.hide_animated()
        else:
            # Posicionar painel
            btn_pos = self.emoji_btn.mapToGlobal(self.emoji_btn.rect().bottomLeft())
            parent_pos = self.mapFromGlobal(btn_pos)

            self.emoji_panel.move(
                parent_pos.x() - self.emoji_panel.width() + self.emoji_btn.width(),
                parent_pos.y() - self.emoji_panel.height() - 10
            )

            self.emoji_panel.show_animated()

            # Conectar seleção de emoji
            if not hasattr(self.emoji_panel, '_connected'):
                self.emoji_panel.emoji_selected.connect(self.insert_emoji)
                self.emoji_panel._connected = True

    def insert_emoji(self, emoji: str):
        """Insere emoji no texto"""
        cursor = self.text_input.textCursor()
        cursor.insertText(emoji)
        self.text_input.setFocus()

    def select_image(self):
        """Seleciona imagem para envio"""
        if not self.current_contact:
            QMessageBox.warning(self, "Aviso", "Selecione um contato primeiro!")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Imagem",
            "",
            "Imagens (*.png *.jpg *.jpeg *.gif *.webp);;Todos os arquivos (*)"
        )

        if file_path:
            self.send_file_message.emit(file_path, "image")

    def select_document(self):
        """Seleciona documento para envio"""
        if not self.current_contact:
            QMessageBox.warning(self, "Aviso", "Selecione um contato primeiro!")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Documento",
            "",
            "Todos os arquivos (*)"
        )

        if file_path:
            self.send_file_message.emit(file_path, "document")

    def select_audio(self):
        """Seleciona arquivo de áudio"""
        if not self.current_contact:
            QMessageBox.warning(self, "Aviso", "Selecione um contato primeiro!")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Áudio",
            "",
            "Áudio (*.mp3 *.wav *.ogg *.m4a *.aac);;Todos os arquivos (*)"
        )

        if file_path:
            self.send_file_message.emit(file_path, "audio")

    def send_location(self):
        """Envia localização atual"""
        if not self.current_contact:
            QMessageBox.warning(self, "Aviso", "Selecione um contato primeiro!")
            return

        # TODO: Implementar seleção de localização real
        # Por enquanto, usar localização padrão
        lat, lng = -23.5505, -46.6333  # São Paulo
        name = "São Paulo, SP"

        self.send_location_message.emit(lat, lng, name)

    def show_progress(self, message: str, value: int = 0):
        """Mostra barra de progresso"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(value)
        self.progress_frame.setVisible(True)

    def update_progress(self, value: int):
        """Atualiza progresso"""
        self.progress_bar.setValue(value)

    def hide_progress(self):
        """Esconde barra de progresso"""
        self.progress_frame.setVisible(False)

    def set_current_contact(self, contact_id: str):
        """Define contato atual"""
        self.current_contact = contact_id

        if contact_id:
            self.text_input.setEnabled(True)
            self.attach_btn.setEnabled(True)
            self.emoji_btn.setEnabled(True)
            self.action_btn.setEnabled(True)

            self.text_input.setPlaceholderText("Digite uma mensagem... 😊")
        else:
            self.text_input.setEnabled(False)
            self.attach_btn.setEnabled(False)
            self.emoji_btn.setEnabled(False)
            self.action_btn.setEnabled(False)

            self.text_input.setPlaceholderText("Selecione um contato para enviar mensagens")

    def clear_input(self):
        """Limpa entrada"""
        self.text_input.clear()

    def focus_input(self):
        """Foca no campo de entrada"""
        self.text_input.setFocus()


# Widget de preview de arquivo antes do envio
class FilePreviewWidget(QWidget):
    """Widget para preview de arquivos antes do envio"""

    send_confirmed = pyqtSignal(str, str, str)  # file_path, file_type, caption
    send_cancelled = pyqtSignal()

    def __init__(self, file_path: str, file_type: str):
        super().__init__()
        self.file_path = file_path
        self.file_type = file_type
        self.setup_ui()

    def setup_ui(self):
        """Configura interface de preview"""
        self.setFixedSize(400, 300)
        self.setWindowTitle("Enviar Arquivo")
        self.setStyleSheet("""
            FilePreviewWidget {
                background-color: white;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        title_label = QLabel(f"Enviar {self.file_type.title()}")
        title_label.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #667eea;")
        layout.addWidget(title_label)

        # Preview do arquivo
        preview_frame = QFrame()
        preview_frame.setFixedHeight(150)
        preview_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 8px;
            }
        """)

        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Ícone e nome do arquivo
        file_name = os.path.basename(self.file_path)
        file_size = os.path.getsize(self.file_path)
        size_mb = file_size / (1024 * 1024)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.file_type == "image":
            icon_label.setText("📷")
            # TODO: Carregar preview da imagem
        elif self.file_type == "audio":
            icon_label.setText("🎵")
        elif self.file_type == "document":
            icon_label.setText("📄")

        icon_label.setStyleSheet("font-size: 48px;")
        preview_layout.addWidget(icon_label)

        name_label = QLabel(file_name)
        name_label.setFont(QFont('Segoe UI', 11, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: #495057;")
        preview_layout.addWidget(name_label)

        size_label = QLabel(f"{size_mb:.2f} MB")
        size_label.setFont(QFont('Segoe UI', 9))
        size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        size_label.setStyleSheet("color: #6c757d;")
        preview_layout.addWidget(size_label)

        layout.addWidget(preview_frame)

        # Campo de legenda (apenas para imagens)
        if self.file_type == "image":
            self.caption_input = QLineEdit()
            self.caption_input.setPlaceholderText("Adicione uma legenda (opcional)")
            self.caption_input.setStyleSheet("""
                QLineEdit {
                    padding: 10px;
                    border: 2px solid #e9ecef;
                    border-radius: 8px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border-color: #667eea;
                }
            """)
            layout.addWidget(self.caption_input)
        else:
            self.caption_input = None

        # Botões
        buttons_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                padding: 0px 20px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        cancel_btn.clicked.connect(self.send_cancelled.emit)

        send_btn = QPushButton("Enviar")
        send_btn.setFixedHeight(40)
        send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                padding: 0px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a6fd8, stop:1 #6a4190);
            }
        """)
        send_btn.clicked.connect(self.confirm_send)

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(send_btn)

        layout.addLayout(buttons_layout)

    def confirm_send(self):
        """Confirma envio do arquivo"""
        caption = ""
        if self.caption_input:
            caption = self.caption_input.text().strip()

        self.send_confirmed.emit(self.file_path, self.file_type, caption)
        self.close()


# Teste do widget
if __name__ == "__main__":
    app = QApplication(sys.argv)

    widget = EnhancedInputWidget()
    widget.set_current_contact("5511999999999")
    widget.show()

    # Conectar sinais para teste
    widget.send_text_message.connect(lambda text: print(f"Texto: {text}"))
    widget.send_file_message.connect(lambda path, type: print(f"Arquivo: {path} ({type})"))
    widget.send_audio_message.connect(lambda path: print(f"Áudio: {path}"))
    widget.send_location_message.connect(lambda lat, lng, name: print(f"Localização: {lat}, {lng} - {name}"))

    sys.exit(app.exec())
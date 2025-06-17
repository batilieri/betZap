#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget de mensagens com integração WhatsAppApi para envios
Suporte a menu de contexto, reações, anexos e REPRODUÇÃO/TRANSCRIÇÃO DE ÁUDIO
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QPushButton, QScrollArea,
    QSizePolicy, QApplication, QMenu, QFileDialog,
    QDialog, QLineEdit, QComboBox, QTextEdit, QWidgetAction, QGridLayout, QMessageBox,
    QProgressBar, QSlider
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer, pyqtSignal, QSize, QPoint, QEvent, \
    QThread, QUrl
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath, QPixmap, QIcon, QAction
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from datetime import datetime
from typing import Dict, Optional, List, Callable
import requests
import tempfile
import os
import base64

# Caminho para imports do WhatsAppApi
import sys

sys.path.append('.')
sys.path.append('./backend')
sys.path.append('./backend/wapi')

# Import condicional do WhatsAppApi
try:
    from WhatsAppApi import WhatsAppAPI
except ImportError:
    try:
        from backend.wapi.__whatsAppApi import WhatsAppAPI
    except ImportError:
        print("⚠️ WhatsAppAPI não encontrada, algumas funcionalidades estarão indisponíveis")

# Imports para transcrição
try:
    import speech_recognition as sr

    SPEECH_RECOGNITION_AVAILABLE = True
    print("✅ SpeechRecognition disponível")
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("⚠️ SpeechRecognition não encontrado. Execute: pip install SpeechRecognition")

try:
    import whisper

    WHISPER_AVAILABLE = True
    print("✅ Whisper disponível")
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Whisper não encontrado. Execute: pip install openai-whisper")

try:
    from pydub import AudioSegment

    PYDUB_AVAILABLE = True
    print("✅ PyDub disponível")
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️ PyDub não encontrado. Execute: pip install pydub")


class AudioDownloadWorker(QThread):
    """Worker para baixar áudio do WhatsApp"""

    download_completed = pyqtSignal(str)  # file_path
    download_failed = pyqtSignal(str)  # error_message
    progress_updated = pyqtSignal(int)  # progress percentage

    def __init__(self, audio_url, filename="audio"):
        super().__init__()
        self.audio_url = audio_url
        self.filename = filename

    def run(self):
        """Baixa o áudio"""
        try:
            self.progress_updated.emit(10)

            # Baixar áudio
            response = requests.get(self.audio_url, stream=True, timeout=30)
            response.raise_for_status()

            self.progress_updated.emit(30)

            # Salvar em arquivo temporário
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"{self.filename}.ogg")

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = 30 + int((downloaded / total_size) * 50)
                            self.progress_updated.emit(progress)

            self.progress_updated.emit(100)

            # Verificar se arquivo foi criado
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                self.download_completed.emit(file_path)
            else:
                self.download_failed.emit("Arquivo baixado está vazio")

        except Exception as e:
            self.download_failed.emit(f"Erro no download: {str(e)}")


class AudioTranscriptionWorker(QThread):
    """Worker para transcrição de áudio"""

    transcription_completed = pyqtSignal(str)  # transcribed_text
    transcription_failed = pyqtSignal(str)  # error_message
    progress_updated = pyqtSignal(int)  # progress percentage

    def __init__(self, audio_file_path, method="whisper"):
        super().__init__()
        self.audio_file_path = audio_file_path
        self.method = method

    def run(self):
        """Executa a transcrição"""
        try:
            self.progress_updated.emit(10)

            if self.method == "whisper" and WHISPER_AVAILABLE:
                self._transcribe_with_whisper()
            elif self.method == "google" and SPEECH_RECOGNITION_AVAILABLE:
                self._transcribe_with_google()
            else:
                self.transcription_failed.emit("Método de transcrição não disponível")

        except Exception as e:
            self.transcription_failed.emit(f"Erro na transcrição: {str(e)}")

    def _transcribe_with_whisper(self):
        """Transcrição usando Whisper (OpenAI)"""
        try:
            self.progress_updated.emit(20)

            # Carregar modelo Whisper (base é um bom equilíbrio)
            model = whisper.load_model("base")

            self.progress_updated.emit(50)

            # Converter para WAV se necessário
            converted_path = self._convert_to_wav()

            self.progress_updated.emit(70)

            # Transcrever
            result = model.transcribe(converted_path, language="pt")

            self.progress_updated.emit(90)

            text = result["text"].strip()

            # Limpar arquivo convertido
            if converted_path != self.audio_file_path:
                try:
                    os.remove(converted_path)
                except:
                    pass

            self.progress_updated.emit(100)

            if text:
                self.transcription_completed.emit(text)
            else:
                self.transcription_failed.emit("Nenhum texto foi detectado no áudio")

        except Exception as e:
            self.transcription_failed.emit(f"Erro Whisper: {str(e)}")

    def _transcribe_with_google(self):
        """Transcrição usando Google Speech Recognition"""
        try:
            self.progress_updated.emit(20)

            # Converter para WAV
            wav_path = self._convert_to_wav()

            self.progress_updated.emit(50)

            # Usar SpeechRecognition
            recognizer = sr.Recognizer()

            with sr.AudioFile(wav_path) as source:
                audio = recognizer.record(source)

            self.progress_updated.emit(70)

            # Transcrever com Google
            text = recognizer.recognize_google(audio, language="pt-BR")

            self.progress_updated.emit(90)

            # Limpar arquivo convertido
            if wav_path != self.audio_file_path:
                try:
                    os.remove(wav_path)
                except:
                    pass

            self.progress_updated.emit(100)

            if text:
                self.transcription_completed.emit(text)
            else:
                self.transcription_failed.emit("Nenhum texto foi detectado")

        except sr.UnknownValueError:
            self.transcription_failed.emit("Não foi possível entender o áudio")
        except sr.RequestError as e:
            self.transcription_failed.emit(f"Erro do serviço Google: {str(e)}")
        except Exception as e:
            self.transcription_failed.emit(f"Erro Google: {str(e)}")

    def _convert_to_wav(self):
        """Converte áudio para WAV usando PyDub"""
        if not PYDUB_AVAILABLE:
            return self.audio_file_path

        try:
            # Detectar formato
            ext = os.path.splitext(self.audio_file_path)[1].lower()

            if ext == ".wav":
                return self.audio_file_path

            # Converter
            if ext == ".ogg":
                audio = AudioSegment.from_ogg(self.audio_file_path)
            elif ext == ".mp3":
                audio = AudioSegment.from_mp3(self.audio_file_path)
            elif ext == ".m4a":
                audio = AudioSegment.from_file(self.audio_file_path, "m4a")
            else:
                audio = AudioSegment.from_file(self.audio_file_path)

            # Salvar como WAV
            wav_path = self.audio_file_path.replace(ext, ".wav")
            audio.export(wav_path, format="wav")

            return wav_path

        except Exception as e:
            print(f"⚠️ Erro na conversão: {e}")
            return self.audio_file_path


class AudioPlayerWidget(QWidget):
    """Widget para reprodução de áudio com controles"""

    transcription_requested = pyqtSignal(str)  # audio_url

    def __init__(self, audio_data, parent=None):
        super().__init__(parent)
        self.audio_data = audio_data
        self.audio_url = audio_data.get('url', '')
        self.duration_seconds = audio_data.get('seconds', 0)
        self.is_ptt = audio_data.get('ptt', False)

        # Player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        # Estado
        self.is_playing = False
        self.is_loaded = False
        self.current_position = 0
        self.local_audio_file = None

        # Workers
        self.download_worker = None
        self.transcription_worker = None

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Configura interface do player"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(8)

        # Ícone de áudio
        audio_icon = QLabel("🎙️" if self.is_ptt else "🎵")
        audio_icon.setFixedSize(24, 24)
        audio_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        audio_icon.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                font-size: 14px;
            }
        """)

        # Botão de play/pause
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(32, 32)
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.play_button.clicked.connect(self.toggle_playback)

        # Slider de progresso
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(self.duration_seconds if self.duration_seconds > 0 else 100)
        self.progress_slider.setValue(0)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 4px;
                background: #ecf0f1;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #2980b9;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: -4px 0;
            }
            QSlider::sub-page:horizontal {
                background: #3498db;
                border-radius: 2px;
            }
        """)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)

        # Info do áudio
        duration_text = f"{self.duration_seconds}s" if self.duration_seconds else "Áudio"
        audio_type = "🎙️ Mensagem de voz" if self.is_ptt else "🎵 Áudio"

        self.audio_info = QLabel(f"{audio_type} • {duration_text}")
        self.audio_info.setFont(QFont('Segoe UI', 9))
        self.audio_info.setStyleSheet("color: #3498db; font-weight: 500;")

        # Botão de transcrição
        self.transcribe_button = QPushButton("📝")
        self.transcribe_button.setFixedSize(28, 28)
        self.transcribe_button.setToolTip("Transcrever áudio")
        self.transcribe_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.transcribe_button.clicked.connect(self.start_transcription)

        # Verificar se transcrição está disponível
        if not (WHISPER_AVAILABLE or SPEECH_RECOGNITION_AVAILABLE):
            self.transcribe_button.setEnabled(False)
            self.transcribe_button.setToolTip("Transcrição não disponível (instale whisper ou speech_recognition)")

        # Montar layout
        layout.addWidget(audio_icon)
        layout.addWidget(self.play_button)
        layout.addWidget(self.progress_slider, 1)
        layout.addWidget(self.audio_info)
        layout.addWidget(self.transcribe_button)

        # Estilo do container
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(52, 152, 219, 0.1);
                border: 1px solid #3498db;
                border-radius: 8px;
                margin: 2px;
            }
        """)

        # Timer para atualizar progresso
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_position)

    def connect_signals(self):
        """Conecta sinais do media player"""
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)

    def toggle_playback(self):
        """Alterna entre play e pause"""
        if not self.is_loaded:
            self.load_audio()
            return

        if self.is_playing:
            self.media_player.pause()
        else:
            self.media_player.play()

    def load_audio(self):
        """Carrega áudio para reprodução"""
        if not self.audio_url:
            QMessageBox.warning(self, "Erro", "URL do áudio não disponível")
            return

        # Desabilitar botão durante carregamento
        self.play_button.setEnabled(False)
        self.play_button.setText("⏳")

        # Iniciar download
        self.download_worker = AudioDownloadWorker(self.audio_url, f"audio_{int(datetime.now().timestamp())}")
        self.download_worker.download_completed.connect(self.on_audio_downloaded)
        self.download_worker.download_failed.connect(self.on_download_failed)
        self.download_worker.progress_updated.connect(self.on_download_progress)
        self.download_worker.start()

    def on_audio_downloaded(self, file_path):
        """Callback quando áudio é baixado"""
        try:
            self.local_audio_file = file_path

            # Carregar no player
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.is_loaded = True

            # Restaurar botão
            self.play_button.setEnabled(True)
            self.play_button.setText("▶")

            # Iniciar reprodução automaticamente
            self.media_player.play()

        except Exception as e:
            self.on_download_failed(f"Erro ao carregar áudio: {str(e)}")

    def on_download_failed(self, error_message):
        """Callback quando download falha"""
        self.play_button.setEnabled(True)
        self.play_button.setText("❌")
        QMessageBox.warning(self, "Erro", f"Falha no download do áudio:\n{error_message}")

    def on_download_progress(self, progress):
        """Callback para progresso do download"""
        self.play_button.setText(f"{progress}%")

    def on_position_changed(self, position):
        """Callback quando posição do áudio muda"""
        self.current_position = position
        if not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position // 1000)  # Converter ms para s

    def on_duration_changed(self, duration):
        """Callback quando duração é conhecida"""
        if duration > 0:
            self.progress_slider.setMaximum(duration // 1000)
            self.duration_seconds = duration // 1000

            # Atualizar info
            audio_type = "🎙️ Mensagem de voz" if self.is_ptt else "🎵 Áudio"
            self.audio_info.setText(f"{audio_type} • {self.duration_seconds}s")

    def on_media_status_changed(self, status):
        """Callback para mudanças no status da mídia"""
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.is_loaded = True
            self.play_button.setEnabled(True)

    def on_playback_state_changed(self, state):
        """Callback para mudanças no estado de reprodução"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.is_playing = True
            self.play_button.setText("⏸")
            self.position_timer.start(100)  # Atualizar a cada 100ms
        else:
            self.is_playing = False
            self.play_button.setText("▶")
            self.position_timer.stop()

    def on_slider_pressed(self):
        """Callback quando slider é pressionado"""
        if self.is_playing:
            self.media_player.pause()

    def on_slider_released(self):
        """Callback quando slider é solto"""
        position = self.progress_slider.value() * 1000  # Converter s para ms
        self.media_player.setPosition(position)

        if self.is_loaded:
            self.media_player.play()

    def update_position(self):
        """Atualiza posição atual"""
        if self.is_playing and not self.progress_slider.isSliderDown():
            position_seconds = self.media_player.position() // 1000
            self.progress_slider.setValue(position_seconds)

    def start_transcription(self):
        """Inicia processo de transcrição"""
        if not self.local_audio_file and self.audio_url:
            # Precisa baixar primeiro
            self.transcribe_button.setEnabled(False)
            self.transcribe_button.setText("⏳")

            # Baixar áudio
            self.download_worker = AudioDownloadWorker(self.audio_url, f"transcribe_{int(datetime.now().timestamp())}")
            self.download_worker.download_completed.connect(self.on_audio_ready_for_transcription)
            self.download_worker.download_failed.connect(self.on_transcription_download_failed)
            self.download_worker.start()

        elif self.local_audio_file:
            # Já temos o arquivo, transcrever diretamente
            self.transcribe_audio_file(self.local_audio_file)
        else:
            QMessageBox.warning(self, "Erro", "Arquivo de áudio não disponível")

    def on_audio_ready_for_transcription(self, file_path):
        """Callback quando áudio está pronto para transcrição"""
        self.local_audio_file = file_path
        self.transcribe_audio_file(file_path)

    def on_transcription_download_failed(self, error_message):
        """Callback quando download para transcrição falha"""
        self.transcribe_button.setEnabled(True)
        self.transcribe_button.setText("📝")
        QMessageBox.warning(self, "Erro", f"Falha no download para transcrição:\n{error_message}")

    def transcribe_audio_file(self, file_path):
        """Executa transcrição do arquivo de áudio"""
        self.transcribe_button.setEnabled(False)
        self.transcribe_button.setText("🔄")

        # Escolher método de transcrição
        method = "whisper" if WHISPER_AVAILABLE else "google"

        # Iniciar transcrição
        self.transcription_worker = AudioTranscriptionWorker(file_path, method)
        self.transcription_worker.transcription_completed.connect(self.on_transcription_completed)
        self.transcription_worker.transcription_failed.connect(self.on_transcription_failed)
        self.transcription_worker.progress_updated.connect(self.on_transcription_progress)
        self.transcription_worker.start()

    def on_transcription_completed(self, transcribed_text):
        """Callback quando transcrição é concluída"""
        self.transcribe_button.setEnabled(True)
        self.transcribe_button.setText("✅")

        # Mostrar resultado da transcrição
        self.show_transcription_result(transcribed_text)

        # Resetar botão após 2 segundos
        QTimer.singleShot(2000, lambda: self.transcribe_button.setText("📝"))

    def on_transcription_failed(self, error_message):
        """Callback quando transcrição falha"""
        self.transcribe_button.setEnabled(True)
        self.transcribe_button.setText("❌")

        QMessageBox.warning(self, "Erro na Transcrição", f"Não foi possível transcrever o áudio:\n{error_message}")

        # Resetar botão após 2 segundos
        QTimer.singleShot(2000, lambda: self.transcribe_button.setText("📝"))

    def on_transcription_progress(self, progress):
        """Callback para progresso da transcrição"""
        self.transcribe_button.setText(f"{progress}%")

    def show_transcription_result(self, transcribed_text):
        """Mostra resultado da transcrição"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel

        dialog = QDialog(self)
        dialog.setWindowTitle("📝 Transcrição do Áudio")
        dialog.setFixedSize(500, 300)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: black;
                font-weight: bold;
                font-size: 14px;
                margin-bottom: 10px;
            }
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                color: #333;
                line-height: 1.4;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton#copyButton {
                background-color: #27ae60;
            }
            QPushButton#copyButton:hover {
                background-color: #219653;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title_label = QLabel("Texto transcrito:")
        layout.addWidget(title_label)

        # Área de texto
        text_area = QTextEdit()
        text_area.setPlainText(transcribed_text)
        text_area.setReadOnly(True)
        layout.addWidget(text_area)

        # Botões
        button_layout = QHBoxLayout()

        copy_button = QPushButton("📋 Copiar")
        copy_button.setObjectName("copyButton")
        copy_button.clicked.connect(lambda: QApplication.clipboard().setText(transcribed_text))

        close_button = QPushButton("✖ Fechar")
        close_button.clicked.connect(dialog.accept)

        button_layout.addWidget(copy_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        dialog.exec()

    def cleanup(self):
        """Limpa recursos ao destruir widget"""
        if self.media_player:
            self.media_player.stop()

        if self.position_timer.isActive():
            self.position_timer.stop()

        # Limpar arquivo temporário
        if self.local_audio_file and os.path.exists(self.local_audio_file):
            try:
                os.remove(self.local_audio_file)
            except:
                pass

    def __del__(self):
        """Destrutor"""
        self.cleanup()


class MessageOptionsButton(QPushButton):
    """Botão de opções da mensagem (3 pontinhos)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.setText("⋮")
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                color: #7f8c8d;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class MessageBubble(QFrame):
    """Balão de mensagem com menu de contexto e opções avançadas"""

    # Sinais para ações em mensagens
    message_deleted = pyqtSignal(str, str)  # webhook_message_id, chat_id
    message_edited = pyqtSignal(str, str, str)  # webhook_message_id, novo_texto, chat_id
    message_reaction = pyqtSignal(str, str, str)  # webhook_message_id, emoji, chat_id

    def __init__(self, message_data: Dict, is_from_me: bool = False, whatsapp_api=None):
        super().__init__()
        self.message_data = message_data
        self.is_from_me = is_from_me
        self.is_fully_setup = False
        self.whatsapp_api = whatsapp_api

        # NOVO: Flags para controle de mensagens temporárias
        self.is_temporary_sent = False
        self.temp_id = None

        # IDs importantes
        self.webhook_message_id = message_data.get('webhook_message_id', message_data.get('message_id', ''))
        self.local_message_id = message_data.get('local_message_id', '')
        self.chat_id = message_data.get('chat_id', '')

        print(f"📝 Criando MessageBubble:")
        print(f"   Webhook ID: {self.webhook_message_id}")
        print(f"   Local ID: {self.local_message_id}")
        print(f"   Chat ID: {self.chat_id}")

        self.setup_ui()
        self.setup_animation()

    def setup_ui(self):
        """Configura a interface do balão com botões de opções"""
        # Configurações básicas do widget
        self.setMaximumWidth(500)
        self.setMinimumHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 15, 5, 15)
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

        # CORREÇÃO: Alinhamento mais extremo e espaços maiores
        if self.is_from_me:
            # Mensagens enviadas - máximo à direita com margem muito grande
            bubble_container.addStretch(25)  # Espaço MUITO maior à esquerda
            bubble_container.addWidget(self.bubble_frame, 0)
            # Margem específica para mensagens enviadas
            main_layout.setContentsMargins(120, 8, 5, 8)  # 120px de margem esquerda
        else:
            # Mensagens recebidas - lado esquerdo com margem muito grande
            bubble_container.addWidget(self.bubble_frame, 0)
            bubble_container.addStretch(25)  # Espaço MUITO maior à direita
            # Margem específica para mensagens recebidas
            main_layout.setContentsMargins(5, 8, 120, 8)  # 120px de margem direita

        main_layout.addLayout(bubble_container)

        # Configurar o layout principal
        self.setLayout(main_layout)

        # Estilo do container principal
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

    def _mark_as_delivered(self):
        """CORRIGIDO: Marca mensagem como entregue com indicador visual"""
        try:
            print(f"✅ Marcando como entregue: {self.webhook_message_id}")

            # Remover status temporário se existir
            if hasattr(self, 'is_temporary_sent'):
                self.is_temporary_sent = False
            if hasattr(self, '_temp_status'):
                self._temp_status = 'delivered'

            # Encontrar e atualizar indicador de status
            self._update_delivery_status_indicator()

        except Exception as e:
            print(f"⚠️ Erro ao marcar como entregue: {e}")

    def _update_delivery_status_indicator(self):
        """NOVO: Atualiza indicador de status de entrega"""
        try:
            if not self.is_from_me:
                return  # Só para mensagens enviadas

            # Procurar layout de status dentro do bubble_frame
            status_layout = self._find_status_layout()
            if not status_layout:
                return

            # Remover indicadores antigos
            self._remove_old_status_indicators(status_layout)

            # Adicionar novo indicador
            status_icon = QLabel("✓✓")
            status_icon.setObjectName('delivery_status_indicator')
            status_icon.setFont(QFont('Segoe UI', 8, QFont.Weight.Bold))
            status_icon.setStyleSheet("""
                QLabel {
                    color: #4CAF50; 
                    background: transparent;
                    margin-left: 3px;
                }
            """)
            status_icon.setToolTip("Entregue")

            # Adicionar ao layout
            status_layout.addWidget(status_icon)

            # Forçar atualização visual
            self.bubble_frame.updateGeometry()
            self.updateGeometry()

            print(f"✅ Indicador de entrega atualizado")

        except Exception as e:
            print(f"⚠️ Erro ao atualizar indicador: {e}")

    def _find_status_layout(self):
        """NOVO: Encontra o layout de status na mensagem"""
        try:
            if not hasattr(self, 'bubble_frame'):
                return None

            bubble_layout = self.bubble_frame.layout()
            if not bubble_layout:
                return None

            # Procurar layout de conteúdo
            content_layout = bubble_layout.itemAt(0)
            if not content_layout or not content_layout.layout():
                return None

            content_layout = content_layout.layout()

            # Procurar último item (deve ser layout de status)
            last_item_index = content_layout.count() - 1
            if last_item_index >= 0:
                last_item = content_layout.itemAt(last_item_index)
                if last_item and last_item.layout():
                    return last_item.layout()

            return None

        except Exception as e:
            print(f"⚠️ Erro ao encontrar layout de status: {e}")
            return None

    def _remove_old_status_indicators(self, status_layout):
        """Remove indicadores antigos"""
        try:
            items_to_remove = []
            for i in range(status_layout.count()):
                item = status_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if hasattr(widget, 'objectName') and widget.objectName() == 'delivery_status_indicator':
                        items_to_remove.append(widget)

            for widget in items_to_remove:
                widget.deleteLater()

        except Exception as e:
            print(f"⚠️ Erro ao remover indicadores: {e}")

    def _create_bubble(self) -> QFrame:
        """Cria o balão da mensagem com suporte a reações existentes"""
        bubble = QFrame()

        # CORREÇÃO: Reduzir largura máxima ainda mais para criar mais espaço lateral
        if self.is_from_me:
            bubble.setMaximumWidth(400)  # Reduzido de 600 para 400
        else:
            bubble.setMaximumWidth(450)  # Reduzido de 650 para 450

        bubble.setMinimumWidth(120)
        bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # Layout do balão
        bubble_layout = QHBoxLayout(bubble)
        bubble_layout.setContentsMargins(20, 12, 20, 12)
        bubble_layout.setSpacing(5)

        # Container para conteúdo principal
        content_container = QVBoxLayout()
        content_container.setSpacing(5)

        # Ícone baseado no tipo da mensagem
        message_type = self.message_data.get('message_type', 'text')
        type_icon = self._get_type_icon(message_type)

        # Conteúdo principal
        content_text = f"{type_icon}{self.message_data.get('content', '')}"

        self.content_label = QLabel(content_text)
        self.content_label.setWordWrap(True)
        self.content_label.setFont(QFont('Segoe UI', 11))
        self.content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.content_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # Cor do texto baseada no tema
        text_color = "#ffffff" if self.is_from_me else "#2c3e50"
        self.content_label.setStyleSheet(f"""
           color: {text_color}; 
           background: transparent; 
           border: none;
           selection-background-color: rgba(255, 255, 255, 0.3);
       """)

        content_container.addWidget(self.content_label)

        # Adicionar informações extras baseadas no tipo - CORRIGIDO PARA ÁUDIO
        if message_type != 'text':
            extra_widget = self._create_media_preview()
            if extra_widget:
                content_container.addWidget(extra_widget)

        # Mostrar reação atual se existir
        if 'reaction' in self.message_data and self.message_data['reaction']:
            reaction_label = QLabel(self.message_data['reaction'])
            reaction_label.setObjectName('reaction_label')
            reaction_label.setStyleSheet("""
               QLabel {
                   background-color: rgba(255, 255, 255, 0.9);
                   border: 1px solid #e9ecef;
                   border-radius: 12px;
                   padding: 4px 8px;
                   font-size: 16px;
                   margin-top: 5px;
               }
           """)
            reaction_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            content_container.addWidget(reaction_label)

        # Verificar se mensagem foi editada
        if self.message_data.get('edited'):
            content_text_with_edit = f"{content_text} ✏️"
            self.content_label.setText(content_text_with_edit)

        # Verificar se mensagem foi deletada
        if self.message_data.get('deleted'):
            self._show_as_deleted()
            return bubble

        # Horário da mensagem e indicador de status
        status_layout = QHBoxLayout()
        timestamp_str = self.message_data.get('timestamp_str', '')

        if timestamp_str:
            self.time_label = QLabel(timestamp_str)
            self.time_label.setFont(QFont('Segoe UI', 8))

            # CORREÇÃO: Alinhamento do horário baseado no remetente
            if self.is_from_me:
                self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            else:
                self.time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

            time_color = "rgba(255,255,255,0.8)" if self.is_from_me else "#7f8c8d"
            self.time_label.setStyleSheet(f"color: {time_color}; background: transparent; margin-top: 3px;")

            status_layout.addWidget(self.time_label, 1)

            # Adicionar indicador de editada se necessário
            if self.message_data.get('edited'):
                edited_indicator = QLabel("editada")
                edited_indicator.setFont(QFont('Segoe UI', 7))
                edited_indicator.setStyleSheet(f"""
                   color: {time_color};
                   font-style: italic;
                   margin-left: 5px;
                   margin-top: 3px;
               """)
                status_layout.addWidget(edited_indicator)

            # Adicionar ícone de status para mensagens enviadas
            if self.is_from_me:
                status_icon = QLabel("✓")  # Checkmark for delivered
                status_icon.setFont(QFont('Segoe UI', 8))
                status_icon.setStyleSheet(f"color: {time_color}; background: transparent;")
                status_layout.addWidget(status_icon)

        content_container.addLayout(status_layout)

        # Adicionar conteúdo principal
        bubble_layout.addLayout(content_container, 1)

        # Botão de opções (3 pontinhos) - não mostrar se deletada
        if not self.message_data.get('deleted'):
            self.options_button = MessageOptionsButton()
            self.options_button.clicked.connect(self.show_options_menu)
            self.options_button.setVisible(False)  # Inicialmente oculto

            bubble_layout.addWidget(self.options_button, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

            # Mostrar botão de opções ao passar o mouse
            bubble.enterEvent = lambda e: self.options_button.setVisible(True) if not self.message_data.get(
                'deleted') else None
            bubble.leaveEvent = lambda e: self.options_button.setVisible(False)

        # Aplicar estilo visual ao balão
        self._apply_bubble_style(bubble)

        # Adicionar sombra suave
        self._add_shadow(bubble)

        return bubble

    def _apply_bubble_style(self, bubble: QFrame):
        """Aplica estilo visual ao balão"""
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
        """Adiciona sombra ao balão"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
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

    def _create_media_preview(self) -> Optional[QWidget]:
        """CORRIGIDO: Cria preview para mensagens de mídia com PLAYER DE ÁUDIO"""
        message_type = self.message_data.get('message_type', 'text')
        media_data = self.message_data.get('media_data', {})

        if not media_data:
            return None

        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 5, 0, 0)
        preview_layout.setSpacing(3)

        if message_type == 'audio':
            # NOVO: Player de áudio completo com reprodução e transcrição
            try:
                # Extrair dados do áudio da mensagem raw
                raw_data = self.message_data.get('raw_webhook_data', {})
                msg_content = raw_data.get('msgContent', {})
                audio_message = msg_content.get('audioMessage', {})

                if audio_message:
                    # Dados do áudio do WhatsApp
                    audio_data = {
                        'url': audio_message.get('url', ''),
                        'seconds': audio_message.get('seconds', 0),
                        'ptt': audio_message.get('ptt', False),
                        'mimetype': audio_message.get('mimetype', 'audio/ogg'),
                        'fileLength': audio_message.get('fileLength', 0),
                        'mediaKey': audio_message.get('mediaKey', ''),
                        'directPath': audio_message.get('directPath', ''),
                        'waveform': audio_message.get('waveform', '')
                    }

                    # Criar player de áudio
                    audio_player = AudioPlayerWidget(audio_data, self)
                    preview_layout.addWidget(audio_player)

                    return preview_widget
                else:
                    # Fallback para formato simples
                    return self._create_simple_audio_preview(media_data, preview_layout)

            except Exception as e:
                print(f"⚠️ Erro ao criar player de áudio: {e}")
                return self._create_simple_audio_preview(media_data, preview_layout)

        elif message_type == 'document':
            # Preview de documento (existente)
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

        elif message_type == 'image':
            # Preview de imagem
            caption = media_data.get('caption', '')
            dimensions = ""

            width = media_data.get('width')
            height = media_data.get('height')
            if width and height:
                dimensions = f" • {width}x{height}"

            img_label = QLabel(f"🖼️ Imagem{dimensions}")
            img_label.setFont(QFont('Segoe UI', 9))
            img_label.setStyleSheet("color: #e74c3c; font-style: italic;")
            preview_layout.addWidget(img_label)

            if caption:
                caption_label = QLabel(f"💬 {caption}")
                caption_label.setFont(QFont('Segoe UI', 8))
                caption_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
                caption_label.setWordWrap(True)
                preview_layout.addWidget(caption_label)

        elif message_type == 'video':
            # Preview de vídeo
            caption = media_data.get('caption', '')

            video_label = QLabel("🎬 Vídeo")
            video_label.setFont(QFont('Segoe UI', 9))
            video_label.setStyleSheet("color: #9b59b6; font-style: italic;")
            preview_layout.addWidget(video_label)

            if caption:
                caption_label = QLabel(f"💬 {caption}")
                caption_label.setFont(QFont('Segoe UI', 8))
                caption_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
                caption_label.setWordWrap(True)
                preview_layout.addWidget(caption_label)

        elif message_type == 'location':
            # Preview de localização
            location_name = media_data.get('name', 'Localização')
            address = media_data.get('address', '')

            location_label = QLabel(f"📍 {location_name}")
            location_label.setFont(QFont('Segoe UI', 9))
            location_label.setStyleSheet("color: #f39c12; font-weight: 500;")
            preview_layout.addWidget(location_label)

            if address:
                address_label = QLabel(address)
                address_label.setFont(QFont('Segoe UI', 8))
                address_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
                address_label.setWordWrap(True)
                preview_layout.addWidget(address_label)

        return preview_widget

    def _create_simple_audio_preview(self, media_data, layout):
        """Cria preview simples de áudio quando player completo falha"""
        audio_container = QWidget()
        audio_layout = QHBoxLayout(audio_container)
        audio_layout.setContentsMargins(8, 5, 8, 5)
        audio_layout.setSpacing(8)

        # Ícone de áudio
        audio_icon = QLabel("🎵")
        audio_icon.setFixedSize(24, 24)
        audio_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        audio_icon.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                font-size: 14px;
            }
        """)

        # Info do áudio
        duration = media_data.get('seconds', 0)
        if duration:
            duration_text = f"{duration}s"
        else:
            duration_text = "Áudio"

        # Detectar se é PTT (Push to Talk)
        is_ptt = media_data.get('ptt', False)
        audio_type = "🎙️ Mensagem de voz" if is_ptt else "🎵 Áudio"

        audio_info = QLabel(f"{audio_type} • {duration_text}")
        audio_info.setFont(QFont('Segoe UI', 9))
        audio_info.setStyleSheet("color: #3498db; font-weight: 500;")

        # Botão de play simples
        play_button = QPushButton("▶")
        play_button.setFixedSize(32, 32)
        play_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        play_button.clicked.connect(lambda: self._simple_audio_placeholder())

        audio_layout.addWidget(audio_icon)
        audio_layout.addWidget(audio_info, 1)
        audio_layout.addWidget(play_button)

        # Container com borda
        audio_container.setStyleSheet("""
            QWidget {
                background-color: rgba(52, 152, 219, 0.1);
                border: 1px solid #3498db;
                border-radius: 8px;
                margin: 2px;
            }
        """)

        layout.addWidget(audio_container)
        return audio_container.parent()

    def _simple_audio_placeholder(self):
        """Placeholder simples para áudio"""
        QMessageBox.information(self, "Áudio",
                                "Player de áudio completo não disponível.\nFuncionalidade básica em desenvolvimento.")

    def setup_animation(self):
        """Configura animação de entrada"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuart)

    def animate_in(self):
        """Anima a entrada do balão"""
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

    def show_options_menu(self):
        """CORRIGIDO: Menu de opções considerando estado temporário"""
        if not self.message_data.get('message_id'):
            return

        # CORREÇÃO: Menu limitado para mensagens temporárias
        if self.is_temporary_sent:
            menu = QMenu(self)
            menu.setStyleSheet("""
               QMenu {
                   background-color: white;
                   border: 1px solid #e0e0e0;
                   border-radius: 8px;
                   padding: 5px;
               }
               QMenu::item {
                   padding: 8px 15px;
                   border-radius: 4px;
                   color: #2c3e50;
                   font-size: 13px;
               }
               QMenu::item:selected {
                   background-color: #f8f9fa;
               }
           """)

            # Apenas opção informativa para mensagens temporárias
            info_action = QAction("⏳ Aguardando confirmação...", self)
            info_action.setEnabled(False)
            menu.addAction(info_action)

            pos = self.options_button.mapToGlobal(QPoint(0, self.options_button.height()))
            menu.exec(pos)
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
           QMenu {
               background-color: white;
               border: 1px solid #e0e0e0;
               border-radius: 8px;
               padding: 5px;
           }
           QMenu::item {
               padding: 8px 15px;
               border-radius: 4px;
               color: #2c3e50;
               font-size: 13px;
           }
           QMenu::item:selected {
               background-color: #f8f9fa;
           }
       """)

        # Opções do menu
        if self.is_from_me:
            edit_action = QAction("Editar mensagem", self)
            edit_action.triggered.connect(self.edit_message)
            menu.addAction(edit_action)

            delete_action = QAction("Deletar mensagem", self)
            delete_action.triggered.connect(self.delete_message)
            menu.addAction(delete_action)

            menu.addSeparator()

        # Submenu de reações
        reactions_menu = QMenu("😀 Reações", menu)
        reactions_menu.setStyleSheet(menu.styleSheet())

        reactions = ["👍", "❤️", "😂", "😮", "😢", "🙏"]
        for reaction in reactions:
            action = QAction(reaction, self)
            action.triggered.connect(lambda checked, r=reaction: self.add_reaction(r))
            reactions_menu.addAction(action)

        # Opção para remover reação
        remove_reaction = QAction("Remover reação", self)
        remove_reaction.triggered.connect(lambda: self.add_reaction(None))
        reactions_menu.addAction(remove_reaction)

        menu.addMenu(reactions_menu)

        # Mostrar menu
        pos = self.options_button.mapToGlobal(QPoint(0, self.options_button.height()))
        menu.exec(pos)

    def edit_message(self):
        """CORRIGIDO: Edição considerando IDs corretos"""
        # CORREÇÃO: Não permitir edição de mensagens temporárias
        if self.is_temporary_sent:
            QMessageBox.warning(self, "Aviso", "Aguarde a confirmação do envio antes de editar.")
            return

        if not self.webhook_message_id or not self.whatsapp_api:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Mensagem")
        dialog.setFixedWidth(400)

        # CORREÇÃO: Forçar background branco no dialog
        dialog.setStyleSheet("""
           QDialog {
               background-color: white;
           }
           QLabel {
               color: black;
               background-color: transparent;
           }
           QTextEdit {
               background-color: white;
               color: black;
               border: 1px solid #ccc;
               border-radius: 5px;
               padding: 8px;
           }
           QPushButton {
               background-color: #3498db;
               color: white;
               border: none;
               border-radius: 5px;
               padding: 8px 16px;
           }
           QPushButton:hover {
               background-color: #2980b9;
           }
       """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Campo de edição
        current_text = self.message_data.get('content', '')
        if current_text.startswith(('🏷️', '📷', '🎥', '🎵', '📄', '📍', '📊', '📱')):
            current_text = current_text[2:].strip()

        edit_field = QTextEdit()
        edit_field.setText(current_text)
        edit_field.setMinimumHeight(100)

        # Botões
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(dialog.reject)

        save_btn = QPushButton("Salvar")
        save_btn.clicked.connect(dialog.accept)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addWidget(QLabel("Editar o texto da mensagem:"))
        layout.addWidget(edit_field)
        layout.addLayout(button_layout)

        # Executar dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_text = edit_field.toPlainText()

            if new_text != current_text and self.whatsapp_api:
                try:
                    phone_number = self.chat_id or self.message_data.get('sender_id', '')

                    result = self.whatsapp_api.editar_mensagem(
                        phone=phone_number,
                        message_id=self.webhook_message_id,
                        new_text=new_text
                    )

                    if result:
                        # Atualizar localmente
                        self.message_data['content'] = new_text
                        self.message_data['edited'] = True
                        self._show_as_edited(new_text)

                        # Emitir sinal
                        self.message_edited.emit(self.webhook_message_id, new_text, self.chat_id)
                    else:
                        QMessageBox.warning(self, "Erro", "Resposta inválida da API ao editar mensagem.")

                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Erro ao editar mensagem: {str(e)}")

    def _show_as_edited(self, new_text: str):
        """Mostra mensagem como editada com marcação visual - CORRIGIDO"""
        try:
            # Atualizar texto com marcação de editada
            message_type = self.message_data.get('message_type', 'text')
            type_icon = self._get_type_icon(message_type)

            edited_text = f"{type_icon}{new_text} ✏️"
            self.content_label.setText(edited_text)

            # Encontrar o layout de status para adicionar marcação
            bubble_layout = self.bubble_frame.layout()
            if bubble_layout:
                content_layout = bubble_layout.itemAt(0).layout()
                if content_layout:
                    # Procurar layout de status
                    for i in range(content_layout.count()):
                        item = content_layout.itemAt(i)
                        if item and item.layout():
                            status_layout = item.layout()

                            # Adicionar indicador de editada
                            if not hasattr(self, 'edited_indicator'):
                                self.edited_indicator = QLabel("editada")
                                self.edited_indicator.setFont(QFont('Segoe UI', 7))

                                # CORREÇÃO: Usar apenas cor sem sobrescrever background
                                time_color = "rgba(255,255,255,0.8)" if self.is_from_me else "#7f8c8d"
                                self.edited_indicator.setStyleSheet(f"""
                                   color: {time_color};
                                   font-style: italic;
                                   margin-left: 5px;
                               """)
                                status_layout.addWidget(self.edited_indicator)
                            break

        except Exception as e:
            print(f"Erro ao marcar como editada: {e}")

    def delete_message(self):
        """CORRIGIDO: Exclusão considerando IDs corretos"""
        # CORREÇÃO: Não permitir exclusão de mensagens temporárias
        if self.is_temporary_sent:
            QMessageBox.warning(self, "Aviso", "Aguarde a confirmação do envio antes de excluir.")
            return

        if not self.webhook_message_id or not self.whatsapp_api:
            print(f"❌ Não é possível deletar - Webhook ID: {self.webhook_message_id}, API: {bool(self.whatsapp_api)}")
            return

        # CORREÇÃO: Dialog de confirmação com background branco forçado
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Deletar Mensagem")
        msg_box.setText("Deseja deletar esta mensagem?")
        msg_box.setInformativeText("Esta ação não pode ser desfeita.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        # CORREÇÃO: Forçar estilo branco no QMessageBox
        msg_box.setStyleSheet("""
           QMessageBox {
               background-color: white;
               color: black;
           }
           QMessageBox QLabel {
               background-color: white;
               color: black;
           }
           QMessageBox QPushButton {
               background-color: #3498db;
               color: white;
               border: none;
               border-radius: 5px;
               padding: 8px 16px;
               min-width: 80px;
           }
           QMessageBox QPushButton:hover {
               background-color: #2980b9;
           }
       """)

        yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
        yes_button.setText("Deletar")
        no_button = msg_box.button(QMessageBox.StandardButton.No)
        no_button.setText("Cancelar")

        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            try:
                phone_number = self.chat_id or self.message_data.get('sender_id', '')

                if not phone_number:
                    QMessageBox.warning(self, "Erro", "Não foi possível identificar o destinatário.")
                    return

                # Fazer a chamada para a API
                result = self.whatsapp_api.deleta_mensagem(
                    phone_number=phone_number,
                    message_ids=[self.webhook_message_id]
                )

                if result and isinstance(result, dict):
                    if result.get('success') or result.get('status') == 'success':
                        print(f"✅ Mensagem deletada com sucesso!")

                        # Marcar como deletada localmente
                        self.message_data['deleted'] = True
                        self._show_as_deleted()

                        # Emitir sinal
                        self.message_deleted.emit(self.webhook_message_id, self.chat_id)
                    else:
                        error_msg = result.get('error', 'Resposta inesperada da API')
                        QMessageBox.warning(self, "Erro", f"Falha ao deletar: {error_msg}")
                else:
                    QMessageBox.warning(self, "Erro", "Resposta inválida da API.")

            except Exception as e:
                print(f"❌ Erro ao deletar mensagem: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao apagar mensagem: {str(e)}")

    def _show_as_deleted(self):
        """Mostra mensagem como deletada mantendo background branco - CORRIGIDO"""
        try:
            # Atualizar conteúdo
            deleted_text = "🗑️ Esta mensagem foi apagada"
            self.content_label.setText(deleted_text)

            # CORREÇÃO: Manter cor de texto sem afetar background
            self.content_label.setStyleSheet("""
               color: #e74c3c; 
               font-style: italic;
           """)

            # CORREÇÃO: Aplicar estilo apenas ao bubble_frame
            if self.is_from_me:
                self.bubble_frame.setStyleSheet("""
                   QFrame {
                       background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                           stop:0 #ff7675, stop:1 #d63031);
                       border-radius: 18px;
                       border-bottom-right-radius: 5px;
                       opacity: 0.8;
                   }
               """)
            else:
                self.bubble_frame.setStyleSheet("""
                   QFrame {
                       background-color: #ffeaea;
                       border: 2px solid #e74c3c;
                       border-radius: 18px;
                       border-bottom-left-radius: 5px;
                       opacity: 0.8;
                   }
               """)

            # Desabilitar menu de opções
            if hasattr(self, 'options_button'):
                self.options_button.setVisible(False)

            # Remover interações
            self.bubble_frame.enterEvent = lambda e: None
            self.bubble_frame.leaveEvent = lambda e: None

        except Exception as e:
            print(f"Erro ao marcar como deletada: {e}")

    def add_reaction(self, reaction: Optional[str]):
        """CORRIGIDO: Reação considerando IDs corretos"""
        # CORREÇÃO: Não permitir reação em mensagens temporárias
        if self.is_temporary_sent:
            QMessageBox.warning(self, "Aviso", "Aguarde a confirmação do envio antes de reagir.")
            return

        if not self.webhook_message_id or not self.whatsapp_api:
            return

        try:
            phone_number = self.chat_id or self.message_data.get('sender_id', '')

            if reaction:
                # Adicionar reação
                result = self.whatsapp_api.enviar_reacao(
                    phone=phone_number,
                    message_id=self.webhook_message_id,
                    reaction=reaction,
                    delay=1
                )
            else:
                # Remover reação
                result = self.whatsapp_api.removerReacao(
                    phone=phone_number,
                    menssagem_id=self.webhook_message_id,
                    dalay=1
                )

            if result:
                # Atualizar estado local IMEDIATAMENTE
                self.message_data['reaction'] = reaction
                self._update_reaction_display(reaction)

                # Emitir sinal
                self.message_reaction.emit(self.webhook_message_id, reaction or '', self.chat_id)
            else:
                QMessageBox.warning(self, "Erro", "Não foi possível aplicar a reação.")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao reagir à mensagem: {str(e)}")

    def _update_reaction_display(self, reaction: Optional[str]):
        """Atualiza a exibição da reação na interface"""
        try:
            # Encontrar layout de conteúdo
            bubble_layout = self.bubble_frame.layout()
            if not bubble_layout:
                return

            content_layout = bubble_layout.itemAt(0).layout()
            if not content_layout:
                return

            # Procurar por reação existente e remover
            for i in range(content_layout.count()):
                item = content_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if hasattr(widget, 'objectName') and widget.objectName() == 'reaction_label':
                        widget.deleteLater()
                        break

            # Adicionar nova reação se existe
            if reaction:
                reaction_label = QLabel(reaction)
                reaction_label.setObjectName('reaction_label')
                reaction_label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(255, 255, 255, 0.9);
                        border: 1px solid #e9ecef;
                        border-radius: 12px;
                        padding: 4px 8px;
                        font-size: 16px;
                        margin-top: 5px;
                    }
                """)
                reaction_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

                # Inserir antes do layout de status (último item)
                insert_position = content_layout.count() - 1
                content_layout.insertWidget(insert_position, reaction_label)

            # Atualizar layout
            self.bubble_frame.updateGeometry()
            self.updateGeometry()

        except Exception as e:
            print(f"Erro ao atualizar reação: {e}")

    def sizeHint(self):
        """Retorna tamanho sugerido do widget"""
        if hasattr(self, 'bubble_frame') and self.bubble_frame:
            bubble_size = self.bubble_frame.sizeHint()
            return bubble_size
        return super().sizeHint()

    def cleanup(self):
        """Limpa recursos quando widget é destruído"""
        # Limpar players de áudio
        try:
            # Procurar por AudioPlayerWidgets no bubble
            if hasattr(self, 'bubble_frame'):
                audio_players = self.bubble_frame.findChildren(AudioPlayerWidget)
                for player in audio_players:
                    player.cleanup()
        except Exception as e:
            print(f"⚠️ Erro ao limpar recursos de áudio: {e}")

    def __del__(self):
        """Destructor"""
        self.cleanup()


class DateSeparator(QWidget):
    """Separador de data entre mensagens"""

    def __init__(self, date_str: str):
        super().__init__()
        self.date_str = date_str
        self.setup_ui()

    def setup_ui(self):
        """Configura o separador de data"""
        self.setFixedHeight(45)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)

        # Linha esquerda
        left_line = QFrame()
        left_line.setFrameStyle(QFrame.Shape.HLine)
        left_line.setStyleSheet("border: 1px solid #e3e6ea;")

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


class AttachmentButton(QPushButton):
    """Botão para anexar arquivos"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setText("📎")
        self.setToolTip("Anexar arquivo")
        self.setStyleSheet("""
            QPushButton {
                background-color: #f1f3f4;
                border-radius: 20px;
                font-size: 18px;
                color: #2c3e50;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)


class FileAttachmentDialog(QDialog):
    """Dialog para seleção e envio de arquivos"""

    def __init__(self, parent=None, whatsapp_api=None, recipient=None):
        super().__init__(parent)
        self.whatsapp_api = whatsapp_api
        self.recipient = recipient
        self.file_path = ""

        self.setup_ui()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("📎 Anexar Arquivo")
        self.setFixedWidth(500)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton#sendButton {
                background-color: #27ae60;
            }
            QPushButton#sendButton:hover {
                background-color: #219653;
            }
            QLabel {
                font-size: 11px;
            }
            QLineEdit, QComboBox, QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Tipo de arquivo
        type_layout = QHBoxLayout()

        type_label = QLabel("Tipo de arquivo:")
        self.file_type = QComboBox()
        self.file_type.addItems([
            "📷 Imagem",
            "📄 Documento",
            "🎵 Áudio",
            "🎬 Vídeo/GIF"
        ])

        type_layout.addWidget(type_label)
        type_layout.addWidget(self.file_type, 1)

        # Caminho do arquivo
        file_layout = QHBoxLayout()

        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setPlaceholderText("Nenhum arquivo selecionado")

        browse_btn = QPushButton("Selecionar")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self.browse_file)

        file_layout.addWidget(QLabel("Arquivo:"))
        file_layout.addWidget(self.file_path_input, 1)
        file_layout.addWidget(browse_btn)

        # Legenda (opcional)
        caption_label = QLabel("Legenda (opcional):")
        self.caption_input = QTextEdit()
        self.caption_input.setMaximumHeight(80)
        self.caption_input.setPlaceholderText("Digite uma legenda para o arquivo...")

        # Botões de ação
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)

        self.send_btn = QPushButton("Enviar")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.clicked.connect(self.accept)
        self.send_btn.setEnabled(False)  # Inicialmente desabilitado

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.send_btn)

        # Montar layout
        layout.addLayout(type_layout)
        layout.addLayout(file_layout)
        layout.addWidget(caption_label)
        layout.addWidget(self.caption_input)
        layout.addLayout(button_layout)

    def browse_file(self):
        """Abre diálogo para selecionar arquivo"""
        file_type = self.file_type.currentText()

        # Definir filtro baseado no tipo
        if "Imagem" in file_type:
            file_filter = "Imagens (*.jpg *.jpeg *.png *.gif);;Todos os arquivos (*.*)"
        elif "Áudio" in file_type:
            file_filter = "Áudio (*.mp3 *.wav *.ogg);;Todos os arquivos (*.*)"
        elif "Vídeo" in file_type:
            file_filter = "Vídeo (*.mp4 *.avi *.mov *.mkv);;GIF (*.gif);;Todos os arquivos (*.*)"
        else:
            file_filter = "Todos os arquivos (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo", "", file_filter
        )

        if file_path:
            self.file_path = file_path
            self.file_path_input.setText(file_path)
            self.send_btn.setEnabled(True)  # Habilitar botão de envio

            # Extrair nome do arquivo para legenda padrão
            import os
            file_name = os.path.basename(file_path)

            # Se for documento, colocar nome como legenda padrão
            if "Documento" in file_type and not self.caption_input.toPlainText():
                self.caption_input.setPlainText(file_name)


class MessageRenderer:
    """Renderizador avançado de mensagens para chat"""

    @staticmethod
    def create_message_widget(message_data: Dict, whatsapp_api=None) -> QWidget:
        """
        Cria widget de mensagem baseado nos dados

        Args:
            message_data: Dados da mensagem do banco
            whatsapp_api: Instância da API do WhatsApp para interações

        Returns:
            Widget da mensagem renderizada
        """
        from_me = message_data.get('from_me', False)

        # Criar balão da mensagem com integração WhatsApp
        message_bubble = MessageBubble(message_data, is_from_me=from_me, whatsapp_api=whatsapp_api)

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


class TypingIndicator(QWidget):
    """Indicador de digitação"""

    def __init__(self, contact_name: str = ""):
        super().__init__()
        self.contact_name = contact_name
        self.setup_ui()

    def setup_ui(self):
        """Configura interface do indicador"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)

        # Cria bolinha de digitação
        typing_widget = QWidget()
        typing_widget.setFixedSize(80, 30)
        typing_widget.setStyleSheet("""
            background-color: #f0f0f0;
            border-radius: 15px;
        """)

        # Layout interno
        typing_layout = QHBoxLayout(typing_widget)
        typing_layout.setContentsMargins(10, 0, 10, 0)
        typing_layout.setSpacing(5)

        # Bolinhas animadas
        for i in range(3):
            dot = QLabel("•")
            dot.setStyleSheet("font-size: 18px; color: #555;")
            typing_layout.addWidget(dot)

            # Animar com timer
            timer = QTimer(dot)
            timer.timeout.connect(lambda d=dot: self._animate_dot(d))
            timer.start(300 + i * 200)

        # Label com nome
        if self.contact_name:
            name_label = QLabel(f"{self.contact_name} está digitando...")
            name_label.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
            layout.addWidget(name_label)
            layout.addStretch(1)

        layout.addWidget(typing_widget)
        layout.addStretch(2)

    def _animate_dot(self, dot: QLabel):
        """Anima uma bolinha"""
        current_opacity = 1.0 if dot.styleSheet().find("opacity") == -1 else 0.3
        new_opacity = 0.3 if current_opacity == 1.0 else 1.0
        dot.setStyleSheet(f"font-size: 18px; color: #555; opacity: {new_opacity};")


class MessagesContainer(QScrollArea):
    """Container otimizado para mensagens"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Configura o container de mensagens"""
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
        self.messages_layout.setContentsMargins(8, 8, 8, 8)
        self.messages_layout.setSpacing(3)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Definir o widget interno
        self.setWidget(self.messages_widget)

    def add_message_widget(self, widget):
        """Adiciona um widget de mensagem ao container"""
        # Garantir que o widget seja visível
        widget.setVisible(True)

        # Adicionar ao layout
        self.messages_layout.addWidget(widget)

        # Atualizar geometria
        self.messages_widget.updateGeometry()

        # Processar eventos
        QApplication.processEvents()

        # Rolar para o final
        QTimer.singleShot(50, self.scroll_to_bottom)

    def clear_messages(self):
        """Limpa todas as mensagens"""
        while self.messages_layout.count() > 0:
            child = self.messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Processar eventos para garantir limpeza
        QApplication.processEvents()

    def scroll_to_bottom(self):
        """Rola para o final das mensagens"""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def add_stretch(self):
        """Adiciona stretch no final para empurrar mensagens para cima"""
        self.messages_layout.addStretch()


class ChatInputArea(QWidget):
    """Área de entrada de mensagens com suporte a anexos e emojis"""

    # Sinais
    message_send = pyqtSignal(str)  # Texto da mensagem
    file_send = pyqtSignal(str, str, str)  # Tipo, caminho, legenda

    def __init__(self, whatsapp_api=None, recipient=None):
        super().__init__()
        self.whatsapp_api = whatsapp_api
        self.recipient = recipient
        self.setup_ui()

    def setup_ui(self):
        """Configura interface do campo de entrada"""
        self.setFixedHeight(70)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-top: 1px solid #e9ecef;
            }
        """)

        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # Botão de anexo
        self.attach_btn = AttachmentButton()
        self.attach_btn.clicked.connect(self.show_attachment_dialog)

        # Campo de texto
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Digite uma mensagem...")
        self.message_input.setMaximumHeight(50)
        self.message_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e9ecef;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 13px;
            }
        """)

        # Conectar Enter para enviar (Shift+Enter para nova linha)
        self.message_input.installEventFilter(self)

        # Botão de emoji
        self.emoji_btn = QPushButton("😀")
        self.emoji_btn.setFixedSize(40, 40)
        self.emoji_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f3f4;
                border-radius: 20px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        self.emoji_btn.clicked.connect(self.show_emoji_picker)

        # Botão de envio
        self.send_btn = QPushButton("📤")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                border-radius: 20px;
                font-size: 18px;
                color: white;
            }
            QPushButton:hover {
                background-color: #219653;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)

        # Montar layout
        layout.addWidget(self.attach_btn)
        layout.addWidget(self.message_input, 1)
        layout.addWidget(self.emoji_btn)
        layout.addWidget(self.send_btn)

    def eventFilter(self, obj, event):
        """Filtro de eventos para detectar Enter no campo de texto"""
        if obj is self.message_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def send_message(self):
        """Envia mensagem de texto"""
        text = self.message_input.toPlainText().strip()
        if text:
            self.message_send.emit(text)
            self.message_input.clear()

    def show_attachment_dialog(self):
        """Mostra diálogo para anexar arquivo"""
        dialog = FileAttachmentDialog(self, self.whatsapp_api, self.recipient)

        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.file_path:
            # Obter tipo selecionado
            file_type = dialog.file_type.currentText()

            # Determinar tipo para API
            if "Imagem" in file_type:
                type_key = "image"
            elif "Documento" in file_type:
                type_key = "document"
            elif "Áudio" in file_type:
                type_key = "audio"
            elif "Vídeo" in file_type:
                type_key = "video"
            else:
                type_key = "document"  # Fallback

            # Emitir sinal com informações do arquivo
            caption = dialog.caption_input.toPlainText()
            self.file_send.emit(type_key, dialog.file_path, caption)

    def show_emoji_picker(self):
        """Mostra seletor de emojis"""
        # Lista de emojis comuns
        emojis = [
            "😀", "😂", "😍", "🤔", "😊", "👍", "❤️", "🎉",
            "🔥", "😎", "🙏", "👏", "🤝", "💪", "🙄", "😢"
        ]

        # Criar menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QMenu::item {
                padding: 8px;
                font-size: 20px;
            }
            QMenu::item:selected {
                background-color: #f0f0f0;
            }
        """)

        # Layout de grade para emojis
        grid_layout = QGridLayout()
        grid_layout.setSpacing(2)

        # Widget para o menu
        grid_widget = QWidget()
        grid_widget.setLayout(grid_layout)

        # Adicionar emojis à grade
        row, col = 0, 0
        for emoji in emojis:
            emoji_btn = QPushButton(emoji)
            emoji_btn.setFixedSize(40, 40)
            emoji_btn.setStyleSheet("QPushButton { border: none; font-size: 20px; }")
            emoji_btn.clicked.connect(lambda checked, e=emoji: self.insert_emoji(e))

            grid_layout.addWidget(emoji_btn, row, col)

            col += 1
            if col > 3:  # 4 colunas
                col = 0
                row += 1

        # Adicionar widget ao menu
        action = QWidgetAction(self)
        action.setDefaultWidget(grid_widget)
        menu.addAction(action)

        # Mostrar menu
        pos = self.emoji_btn.mapToGlobal(QPoint(0, -menu.sizeHint().height()))
        menu.exec(pos)

    def insert_emoji(self, emoji: str):
        """Insere emoji no campo de texto"""
        cursor = self.message_input.textCursor()
        cursor.insertText(emoji)

    def set_recipient(self, recipient: str):
        """Define destinatário atual"""
        self.recipient = recipient

    def set_whatsapp_api(self, api):
        """Define instância da API"""
        self.whatsapp_api = api


class ChatHeader(QWidget):
    """Cabeçalho do chat com informações do contato"""

    refresh_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Configura interface do cabeçalho"""
        self.setFixedHeight(70)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        # Avatar do contato
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(45, 45)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                color: #3498db;
                border-radius: 22px;
                font-weight: bold;
                font-size: 16px;
            }
        """)

        # Informações do contato
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.contact_name = QLabel("Selecione um contato")
        self.contact_name.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        self.contact_name.setStyleSheet("color: white; margin: 0;")

        self.contact_status = QLabel("")
        self.contact_status.setFont(QFont('Segoe UI', 9))
        self.contact_status.setStyleSheet("color: #ecf0f1; margin: 0;")

        info_layout.addWidget(self.contact_name)
        info_layout.addWidget(self.contact_status)

        # Botão de atualização
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(35, 35)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 17px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_clicked)

        # Montar layout
        layout.addWidget(self.avatar_label)
        layout.addLayout(info_layout, 1)
        layout.addStretch()
        layout.addWidget(self.refresh_btn)

    def update_chat_info(self, chat_data: Dict):
        """Atualiza informações do chat no cabeçalho"""
        # Nome do contato
        chat_name = chat_data.get('chat_name', 'Chat')
        self.contact_name.setText(chat_name)

        # Avatar (primeira letra)
        initial = chat_name[0].upper() if chat_name else '?'
        self.avatar_label.setText(initial)

        # Status
        chat_type = chat_data.get('chat_type', 'individual')
        total_msgs = chat_data.get('total_messages', 0)

        if chat_type == 'group':
            participants = chat_data.get('participants_count', 0)
            status_text = f"Grupo • {participants} participantes • {total_msgs} mensagens"
        else:
            status_text = f"Contato • {total_msgs} mensagens"

        self.contact_status.setText(status_text)

# =============================================================================
# 🎵 FUNCIONALIDADES DE ÁUDIO IMPLEMENTADAS
# =============================================================================
#
# 📋 PRINCIPAIS RECURSOS ADICIONADOS:
# ✅ AudioPlayerWidget - Player completo de áudio
# ✅ AudioDownloadWorker - Download assíncrono de áudio do WhatsApp
# ✅ AudioTranscriptionWorker - Transcrição usando Whisper ou Google
# ✅ Reprodução com controles (play/pause/seek)
# ✅ Indicador de progresso visual
# ✅ Transcrição automática com múltiplos engines
# ✅ Suporte a múltiplos formatos (OGG, MP3, M4A, WAV)
# ✅ Interface moderna com botões interativos
#
# 🔧 DEPENDÊNCIAS NECESSÁRIAS:
# pip install pyqt6
# pip install requests
# pip install pydub
# pip install SpeechRecognition
# pip install openai-whisper
#
# 🎯 FUNCIONALIDADES:
# • Reprodução de áudio com player nativo do Qt
# • Download automático de áudios do WhatsApp
# • Transcrição usando Whisper (OpenAI) ou Google Speech
# • Controles de reprodução (play/pause/seek)
# • Indicador visual de progresso
# • Suporte a mensagens de voz (PTT) e áudios normais
# • Interface responsiva com feedback visual
# • Limpeza automática de arquivos temporários
#
# 🚀 COMO USAR:
# 1. Mensagens de áudio aparecerão com player completo
# 2. Clique em ▶ para reproduzir
# 3. Use a barra de progresso para navegar
# 4. Clique em 📝 para transcrever o áudio
# 5. Resultado da transcrição aparece em dialog
#
# ⚙️ CONFIGURAÇÃO:
# • O sistema detecta automaticamente engines disponíveis
# • Whisper é preferido quando disponível
# • Fallback para Google Speech Recognition
# • Suporte a conversão automática de formatos
#
# =============================================================================
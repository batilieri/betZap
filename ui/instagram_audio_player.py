#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AudioPlayerWidget MODERNO - Estilo Instagram
Player de áudio redesenhado com visual moderno e funcionalidades completas
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QProgressBar, QSlider, QFrame, QGraphicsDropShadowEffect,
    QApplication, QMessageBox, QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal, QThread, QUrl
from PyQt6.QtGui import QFont, QColor, QPainter, QPainterPath, QPixmap, QPalette
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from datetime import datetime
import requests
import tempfile
import os
import base64

# Imports para transcrição
try:
    import speech_recognition as sr

    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    from pydub import AudioSegment

    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


class WaveformWidget(QWidget):
    """Widget personalizado para visualização de forma de onda"""

    def __init__(self, waveform_data=None):
        super().__init__()
        self.waveform_data = waveform_data or []
        self.progress = 0.0
        self.setFixedHeight(32)
        self.setMinimumWidth(120)

        # Gerar dados fake se não tiver waveform real
        if not self.waveform_data:
            import random
            self.waveform_data = [random.randint(3, 25) for _ in range(40)]

    def set_progress(self, progress):
        """Define progresso da reprodução (0.0 a 1.0)"""
        self.progress = max(0.0, min(1.0, progress))
        self.update()

    def paintEvent(self, event):
        """Desenha a forma de onda"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Configurações
        width = self.width()
        height = self.height()
        bar_width = max(2, width // len(self.waveform_data))
        spacing = 1

        # Cores
        played_color = QColor("#1DB954")  # Verde Spotify/Instagram
        unplayed_color = QColor("#E1E1E1")

        # Desenhar barras
        x = 0
        progress_x = width * self.progress

        for i, amplitude in enumerate(self.waveform_data):
            if x >= width:
                break

            # Altura da barra baseada na amplitude
            bar_height = (amplitude / 30.0) * height
            y = (height - bar_height) / 2

            # Cor baseada no progresso
            color = played_color if x < progress_x else unplayed_color
            painter.fillRect(x, y, bar_width - spacing, bar_height, color)

            x += bar_width

        painter.end()

    def mousePressEvent(self, event):
        """Permite buscar posição clicando na waveform"""
        if self.width() > 0:
            progress = event.position().x() / self.width()
            self.progress = max(0.0, min(1.0, progress))
            self.update()
            # Emitir sinal personalizado se necessário
            if hasattr(self.parent(), 'seek_to_position'):
                self.parent().seek_to_position(self.progress)


class ModernAudioDownloadWorker(QThread):
    """Worker melhorado para download de áudio"""

    download_completed = pyqtSignal(str, dict)  # file_path, metadata
    download_failed = pyqtSignal(str)
    progress_updated = pyqtSignal(int)

    def __init__(self, audio_url, metadata=None):
        super().__init__()
        self.audio_url = audio_url
        self.metadata = metadata or {}
        self.should_stop = False

    def run(self):
        """Download otimizado com melhor tratamento"""
        try:
            print(f"🎵 Iniciando download: {self.audio_url[:50]}...")
            self.progress_updated.emit(10)

            headers = {
                'User-Agent': 'WhatsApp/2.23.20.0',
                'Accept': 'audio/*,*/*;q=0.9',
                'Connection': 'keep-alive',
            }

            response = requests.get(
                self.audio_url,
                stream=True,
                timeout=30,
                headers=headers,
                verify=False  # WhatsApp pode ter certificados específicos
            )
            response.raise_for_status()

            self.progress_updated.emit(30)

            # Determinar formato
            content_type = response.headers.get('content-type', '').lower()
            if 'opus' in content_type or 'ogg' in content_type:
                extension = '.ogg'
            elif 'mpeg' in content_type or 'mp3' in content_type:
                extension = '.mp3'
            else:
                extension = '.opus'  # WhatsApp padrão

            # Salvar arquivo
            timestamp = int(datetime.now().timestamp())
            filename = f"whatsapp_audio_{timestamp}{extension}"
            file_path = os.path.join(tempfile.gettempdir(), filename)

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.should_stop:
                        return

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = 30 + int((downloaded / total_size) * 60)
                            self.progress_updated.emit(min(progress, 90))

            # Verificar arquivo
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                self.download_failed.emit("Arquivo inválido após download")
                return

            # Tentar converter para formato compatível
            converted_path = self._convert_audio(file_path)

            self.progress_updated.emit(100)

            # Metadados do arquivo
            file_metadata = {
                'original_path': file_path,
                'converted_path': converted_path,
                'size': os.path.getsize(converted_path),
                'format': os.path.splitext(converted_path)[1],
                'duration': self.metadata.get('seconds', 0)
            }

            self.download_completed.emit(converted_path, file_metadata)

        except Exception as e:
            self.download_failed.emit(f"Erro no download: {str(e)}")

    def _convert_audio(self, file_path):
        """Converte áudio para formato compatível"""
        try:
            if not PYDUB_AVAILABLE:
                return file_path

            # Verificar se é OGG/Opus
            if not file_path.lower().endswith('.ogg'):
                return file_path

            print("🔄 Convertendo áudio para MP3...")

            # Tentar conversão
            try:
                audio = AudioSegment.from_ogg(file_path)
            except:
                try:
                    audio = AudioSegment.from_file(file_path)
                except:
                    return file_path

            # Converter para MP3
            mp3_path = file_path.replace('.ogg', '.mp3').replace('.opus', '.mp3')

            audio.export(
                mp3_path,
                format="mp3",
                bitrate="128k",
                parameters=["-ar", "44100", "-ac", "2"]
            )

            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                # Remover arquivo original
                try:
                    os.remove(file_path)
                except:
                    pass
                return mp3_path

            return file_path

        except Exception as e:
            print(f"⚠️ Erro na conversão: {e}")
            return file_path

    def stop(self):
        self.should_stop = True


class ModernTranscriptionWorker(QThread):
    """Worker melhorado para transcrição"""

    transcription_completed = pyqtSignal(str, float)  # text, confidence
    transcription_failed = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)  # progress, status

    def __init__(self, audio_file_path, method="whisper"):
        super().__init__()
        self.audio_file_path = audio_file_path
        self.method = method

    def run(self):
        """Transcrição otimizada"""
        try:
            self.progress_updated.emit(10, "Preparando áudio...")

            if self.method == "whisper" and WHISPER_AVAILABLE:
                self._transcribe_with_whisper()
            elif self.method == "google" and SPEECH_RECOGNITION_AVAILABLE:
                self._transcribe_with_google()
            else:
                self.transcription_failed.emit("Nenhum engine de transcrição disponível")

        except Exception as e:
            self.transcription_failed.emit(f"Erro na transcrição: {str(e)}")

    def _transcribe_with_whisper(self):
        """Transcrição com Whisper melhorada"""
        try:
            import whisper

            self.progress_updated.emit(20, "Carregando modelo Whisper...")

            # Usar modelo otimizado
            model = whisper.load_model("base")

            self.progress_updated.emit(50, "Processando áudio...")

            # Transcrever com configurações otimizadas
            result = model.transcribe(
                self.audio_file_path,
                language="pt",
                fp16=False,
                verbose=False,
                word_timestamps=True  # Para melhor precisão
            )

            self.progress_updated.emit(90, "Finalizando...")

            text = result.get("text", "").strip()

            # Calcular confiança baseada nos segments
            segments = result.get("segments", [])
            if segments:
                avg_confidence = sum(seg.get("avg_logprob", 0) for seg in segments) / len(segments)
                confidence = max(0, min(1, (avg_confidence + 1) / 2))  # Normalizar
            else:
                confidence = 0.5

            if text:
                self.transcription_completed.emit(text, confidence)
            else:
                self.transcription_failed.emit("Nenhum texto detectado")

        except Exception as e:
            self.transcription_failed.emit(f"Erro Whisper: {str(e)}")

    def _transcribe_with_google(self):
        """Transcrição com Google melhorada"""
        try:
            import speech_recognition as sr

            self.progress_updated.emit(30, "Preparando Google Speech...")

            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True

            # Converter para WAV se necessário
            wav_path = self._ensure_wav_format()

            self.progress_updated.emit(60, "Processando com Google...")

            with sr.AudioFile(wav_path) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.record(source)

            text = recognizer.recognize_google(
                audio,
                language="pt-BR",
                show_all=False
            )

            # Limpar arquivo temporário
            if wav_path != self.audio_file_path:
                try:
                    os.remove(wav_path)
                except:
                    pass

            if text:
                self.transcription_completed.emit(text, 0.8)  # Confiança padrão Google
            else:
                self.transcription_failed.emit("Nenhum texto detectado")

        except sr.UnknownValueError:
            self.transcription_failed.emit("Não foi possível entender o áudio")
        except Exception as e:
            self.transcription_failed.emit(f"Erro Google: {str(e)}")

    def _ensure_wav_format(self):
        """Garante que áudio está em formato WAV"""
        if self.audio_file_path.lower().endswith('.wav'):
            return self.audio_file_path

        if not PYDUB_AVAILABLE:
            return self.audio_file_path

        try:
            audio = AudioSegment.from_file(self.audio_file_path)
            wav_path = self.audio_file_path.replace(
                os.path.splitext(self.audio_file_path)[1],
                '.wav'
            )

            audio.export(wav_path, format="wav")
            return wav_path
        except:
            return self.audio_file_path


class InstagramStyleAudioPlayer(QWidget):
    """Player de áudio estilo Instagram - MODERNO E FUNCIONAL"""

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
        self.file_metadata = {}

        # Workers
        self.download_worker = None
        self.transcription_worker = None

        # UI
        self.setup_modern_ui()
        self.connect_signals()

        # Animações
        self.setup_animations()

    def setup_modern_ui(self):
        """Interface moderna estilo Instagram"""
        # Container principal
        self.setFixedHeight(56)
        self.setMinimumWidth(200)

        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(12)

        # === BOTÃO PLAY MODERNO ===
        self.play_button = self._create_modern_play_button()

        # === CONTAINER CENTRAL ===
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(4)

        # Info do áudio
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Ícone + tipo
        type_icon = "🎙️" if self.is_ptt else "🎵"
        self.type_label = QLabel(type_icon)
        self.type_label.setFixedSize(20, 20)
        self.type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.type_label.setStyleSheet("""
            QLabel {
                color: #1DB954;
                font-size: 16px;
                background: transparent;
            }
        """)

        # Texto do tipo
        type_text = "Mensagem de voz" if self.is_ptt else "Áudio"
        self.info_label = QLabel(type_text)
        self.info_label.setFont(QFont('Segoe UI', 9, QFont.Weight.Medium))
        self.info_label.setStyleSheet("color: #262626; background: transparent;")

        # Duração
        duration_text = self._format_duration(self.duration_seconds)
        self.duration_label = QLabel(duration_text)
        self.duration_label.setFont(QFont('Segoe UI', 8))
        self.duration_label.setStyleSheet("color: #8E8E8E; background: transparent;")

        info_layout.addWidget(self.type_label)
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        info_layout.addWidget(self.duration_label)

        # Waveform
        waveform_data = self._extract_waveform_data()
        self.waveform = WaveformWidget(waveform_data)
        self.waveform.parent = lambda: self  # Para callback

        center_layout.addLayout(info_layout)
        center_layout.addWidget(self.waveform)

        # === BOTÕES DE AÇÃO ===
        actions_widget = QWidget()
        actions_layout = QVBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(4)

        # Botão de transcrição
        self.transcribe_button = self._create_transcribe_button()

        # Status/Progresso
        self.status_label = QLabel("")
        self.status_label.setFont(QFont('Segoe UI', 7))
        self.status_label.setStyleSheet("color: #8E8E8E; background: transparent;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        actions_layout.addWidget(self.transcribe_button)
        actions_layout.addWidget(self.status_label)

        # === MONTAGEM FINAL ===
        main_layout.addWidget(self.play_button)
        main_layout.addWidget(center_widget, 1)
        main_layout.addWidget(actions_widget)

        # Estilo do container
        self.setStyleSheet("""
            InstagramStyleAudioPlayer {
                background: #FAFAFA;
                border: 1px solid #DBDBDB;
                border-radius: 18px;
            }
            InstagramStyleAudioPlayer:hover {
                background: #F5F5F5;
                border-color: #C7C7C7;
            }
        """)

        # Sombra sutil
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(6)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 1)
        self.setGraphicsEffect(shadow)

    def _create_modern_play_button(self):
        """Cria botão de play moderno"""
        button = QPushButton("▶")
        button.setFixedSize(40, 40)
        button.clicked.connect(self.toggle_playback)

        button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1DB954, stop:1 #1ED760);
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1ED760, stop:1 #1DB954);
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background: #169C46;
            }
            QPushButton:disabled {
                background: #E0E0E0;
                color: #BDBDBD;
            }
        """)

        return button

    def _create_transcribe_button(self):
        """Cria botão de transcrição moderno"""
        button = QPushButton("📝")
        button.setFixedSize(32, 24)
        button.setToolTip("Transcrever áudio")
        button.clicked.connect(self.start_transcription)

        if not (WHISPER_AVAILABLE or SPEECH_RECOGNITION_AVAILABLE):
            button.setEnabled(False)
            button.setToolTip("Transcrição não disponível")

        button.setStyleSheet("""
            QPushButton {
                background: #E1306C;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #C13584;
            }
            QPushButton:disabled {
                background: #E0E0E0;
                color: #BDBDBD;
            }
        """)

        return button

    def _extract_waveform_data(self):
        """Extrai dados da waveform do áudio"""
        waveform_b64 = self.audio_data.get('waveform', '')

        if waveform_b64:
            try:
                # Decodificar base64
                waveform_bytes = base64.b64decode(waveform_b64)
                # Converter para lista de amplitudes
                waveform_data = [b for b in waveform_bytes[:40]]  # Primeiros 40 pontos
                return waveform_data
            except:
                pass

        # Gerar waveform fake baseada na duração
        import random
        num_bars = min(60, max(20, self.duration_seconds * 10))
        return [random.randint(5, 30) for _ in range(num_bars)]

    def _format_duration(self, seconds):
        """Formata duração em mm:ss"""
        if seconds <= 0:
            return "0:00"

        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"

    def setup_animations(self):
        """Configura animações"""
        # Animação do botão play
        self.play_animation = QPropertyAnimation(self.play_button, b"geometry")
        self.play_animation.setDuration(150)
        self.play_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def connect_signals(self):
        """Conecta sinais do media player"""
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.media_player.errorOccurred.connect(self.on_player_error)

    def toggle_playback(self):
        """Alterna reprodução"""
        if not self.is_loaded:
            self.load_audio()
            return

        if self.is_playing:
            self.media_player.pause()
        else:
            self.media_player.play()

    def load_audio(self):
        """Carrega áudio"""
        if not self.audio_url:
            self.show_error("URL do áudio não disponível")
            return

        self.play_button.setEnabled(False)
        self.play_button.setText("⏳")
        self.status_label.setText("Carregando...")

        # Iniciar download
        self.download_worker = ModernAudioDownloadWorker(self.audio_url, self.audio_data)
        self.download_worker.download_completed.connect(self.on_audio_downloaded)
        self.download_worker.download_failed.connect(self.on_download_failed)
        self.download_worker.progress_updated.connect(self.on_download_progress)
        self.download_worker.start()

    def on_audio_downloaded(self, file_path, metadata):
        """Áudio baixado com sucesso"""
        try:
            self.local_audio_file = file_path
            self.file_metadata = metadata

            # Carregar no player
            file_url = QUrl.fromLocalFile(os.path.abspath(file_path))
            self.media_player.setSource(file_url)
            self.is_loaded = True

            # Restaurar interface
            self.play_button.setEnabled(True)
            self.play_button.setText("▶")
            self.status_label.setText("Pronto")

            print(f"✅ Áudio carregado: {metadata}")

        except Exception as e:
            self.on_download_failed(f"Erro ao carregar: {str(e)}")

    def on_download_failed(self, error):
        """Falha no download"""
        self.play_button.setEnabled(True)
        self.play_button.setText("❌")
        self.status_label.setText("Erro")
        print(f"❌ Erro no download: {error}")

    def on_download_progress(self, progress):
        """Progresso do download"""
        self.status_label.setText(f"Baixando {progress}%")

    def on_position_changed(self, position):
        """Posição mudou"""
        if self.duration_seconds > 0:
            progress = position / (self.duration_seconds * 1000)
            self.waveform.set_progress(progress)

            # Atualizar duração mostrada
            current_seconds = position // 1000
            remaining_seconds = self.duration_seconds - current_seconds
            self.duration_label.setText(f"-{self._format_duration(remaining_seconds)}")

    def on_duration_changed(self, duration_ms):
        """Duração conhecida"""
        if duration_ms > 0:
            self.duration_seconds = duration_ms // 1000

    def on_playback_state_changed(self, state):
        """Estado de reprodução mudou"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.is_playing = True
            self.play_button.setText("⏸")
            self.status_label.setText("Reproduzindo")
        else:
            self.is_playing = False
            self.play_button.setText("▶")
            if state == QMediaPlayer.PlaybackState.PausedState:
                self.status_label.setText("Pausado")
            else:
                self.status_label.setText("Parado")

    def on_player_error(self, error):
        """Erro no player"""
        self.play_button.setText("❌")
        self.status_label.setText("Erro no player")
        print(f"❌ Erro no media player: {error}")

    def seek_to_position(self, progress):
        """Busca posição específica"""
        if self.is_loaded and self.duration_seconds > 0:
            position_ms = int(progress * self.duration_seconds * 1000)
            self.media_player.setPosition(position_ms)

    def start_transcription(self):
        """Inicia transcrição"""
        if not self.local_audio_file:
            if self.audio_url:
                self.transcribe_button.setText("⏳")
                self.transcribe_button.setEnabled(False)

                # Baixar primeiro
                self.download_worker = ModernAudioDownloadWorker(self.audio_url, self.audio_data)
                self.download_worker.download_completed.connect(self.on_audio_ready_for_transcription)
                self.download_worker.download_failed.connect(self.on_transcription_download_failed)
                self.download_worker.start()
            else:
                self.show_error("Áudio não disponível para transcrição")
        else:
            self.transcribe_audio_file(self.local_audio_file)

    def on_audio_ready_for_transcription(self, file_path, metadata):
        """Áudio pronto para transcrição"""
        self.local_audio_file = file_path
        self.transcribe_audio_file(file_path)

    def on_transcription_download_failed(self, error):
        """Falha no download para transcrição"""
        self.transcribe_button.setText("❌")
        self.show_error(f"Erro no download: {error}")
        QTimer.singleShot(2000, lambda: self.transcribe_button.setText("📝"))

    def transcribe_audio_file(self, file_path):
        """Executa transcrição"""
        self.transcribe_button.setEnabled(False)
        self.transcribe_button.setText("🔄")

        # Escolher método
        method = "whisper" if WHISPER_AVAILABLE else "google"

        self.transcription_worker = ModernTranscriptionWorker(file_path, method)
        self.transcription_worker.transcription_completed.connect(self.on_transcription_completed)
        self.transcription_worker.transcription_failed.connect(self.on_transcription_failed)
        self.transcription_worker.progress_updated.connect(self.on_transcription_progress)
        self.transcription_worker.start()

    def on_transcription_completed(self, text, confidence):
        """Transcrição concluída"""
        self.transcribe_button.setEnabled(True)
        self.transcribe_button.setText("✅")

        # Mostrar resultado
        self.show_transcription_result(text, confidence)

        # Resetar botão
        QTimer.singleShot(3000, lambda: self.transcribe_button.setText("📝"))

    def on_transcription_failed(self, error):
        """Transcrição falhou"""
        self.transcribe_button.setEnabled(True)
        self.transcribe_button.setText("❌")
        self.show_error(f"Erro na transcrição: {error}")
        QTimer.singleShot(2000, lambda: self.transcribe_button.setText("📝"))

    def on_transcription_progress(self, progress, status):
        """Progresso da transcrição"""
        self.status_label.setText(status)

    def show_transcription_result(self, text, confidence):
        """Mostra resultado da transcrição em dialog moderno"""
        dialog = ModernTranscriptionDialog(text, confidence, self)
        dialog.exec()

    def show_error(self, message):
        """Mostra erro"""
        QMessageBox.warning(self, "Erro", message)

    def cleanup(self):
        """Limpa recursos"""
        try:
            if self.media_player:
                self.media_player.stop()

            # Parar workers
            if self.download_worker and self.download_worker.isRunning():
                self.download_worker.stop()
                self.download_worker.wait()

            if self.transcription_worker and self.transcription_worker.isRunning():
                self.transcription_worker.terminate()
                self.transcription_worker.wait()

            # Limpar arquivo temporário
            if self.local_audio_file and os.path.exists(self.local_audio_file):
                try:
                    os.remove(self.local_audio_file)
                except:
                    pass

        except Exception as e:
            print(f"⚠️ Erro ao limpar recursos: {e}")


class ModernTranscriptionDialog(QDialog):
    """Dialog moderno para exibir transcrição"""

    def __init__(self, text, confidence, parent=None):
        super().__init__(parent)
        self.text = text
        self.confidence = confidence
        self.setup_ui()

    def setup_ui(self):
        """Interface moderna do dialog"""
        self.setWindowTitle("📝 Transcrição do Áudio")
        self.setFixedSize(520, 350)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FAFAFA, stop:1 #F0F0F0);
                border-radius: 12px;
            }
            QLabel {
                color: #262626;
                background: transparent;
            }
            QTextEdit {
                background: white;
                border: 2px solid #E1E1E1;
                border-radius: 12px;
                padding: 16px;
                font-size: 14px;
                color: #262626;
                line-height: 1.5;
                selection-background-color: #1DB954;
                selection-color: white;
            }
            QTextEdit:focus {
                border-color: #1DB954;
            }
            QPushButton {
                background: #1DB954;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: #1ED760;
            }
            QPushButton:pressed {
                background: #169C46;
            }
            QPushButton#closeButton {
                background: #E0E0E0;
                color: #262626;
            }
            QPushButton#closeButton:hover {
                background: #D0D0D0;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Cabeçalho
        header_layout = QHBoxLayout()

        title_label = QLabel("🎙️ Transcrição do Áudio")
        title_label.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))

        # Indicador de confiança
        confidence_percent = int(self.confidence * 100)
        if confidence_percent >= 80:
            confidence_color = "#1DB954"
            confidence_icon = "✅"
        elif confidence_percent >= 60:
            confidence_color = "#FF9500"
            confidence_icon = "⚠️"
        else:
            confidence_color = "#FF3B30"
            confidence_icon = "❌"

        confidence_label = QLabel(f"{confidence_icon} {confidence_percent}%")
        confidence_label.setFont(QFont('Segoe UI', 11, QFont.Weight.Medium))
        confidence_label.setStyleSheet(f"color: {confidence_color}; background: transparent;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(confidence_label)

        # Área de texto
        self.text_area = QTextEdit()
        self.text_area.setPlainText(self.text)
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont('Segoe UI', 13))

        # Botões
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        copy_button = QPushButton("📋 Copiar Texto")
        copy_button.clicked.connect(self.copy_text)

        select_all_button = QPushButton("🔘 Selecionar Tudo")
        select_all_button.clicked.connect(self.text_area.selectAll)

        close_button = QPushButton("✖ Fechar")
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self.accept)

        button_layout.addWidget(copy_button)
        button_layout.addWidget(select_all_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        # Layout final
        layout.addLayout(header_layout)
        layout.addWidget(self.text_area)
        layout.addLayout(button_layout)

        # Adicionar sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def copy_text(self):
        """Copia texto para clipboard"""
        QApplication.clipboard().setText(self.text)

        # Feedback visual
        self.sender().setText("✅ Copiado!")
        QTimer.singleShot(1500, lambda: self.sender().setText("📋 Copiar Texto"))


def create_instagram_style_audio_preview(message_data):
    """
    Função para criar preview de áudio estilo Instagram
    Para usar no chat_widget.py
    """
    try:
        # Extrair dados de áudio
        audio_data = None

        # Estrutura 1: media_data direto
        if 'media_data' in message_data and message_data['media_data']:
            media_data = message_data['media_data']
            if 'url' in media_data:
                audio_data = media_data

        # Estrutura 2: raw_webhook_data
        if not audio_data and 'raw_webhook_data' in message_data:
            raw_data = message_data['raw_webhook_data']
            msg_content = raw_data.get('msgContent', {})
            audio_message = msg_content.get('audioMessage', {})

            if audio_message:
                audio_data = {
                    'url': audio_message.get('url', ''),
                    'seconds': audio_message.get('seconds', 0),
                    'ptt': audio_message.get('ptt', False),
                    'mimetype': audio_message.get('mimetype', 'audio/ogg'),
                    'fileLength': audio_message.get('fileLength', 0),
                    'waveform': audio_message.get('waveform', '')
                }

        # Estrutura 3: dados básicos
        if not audio_data:
            content = message_data.get('content', '')
            import re
            seconds_match = re.search(r'(\d+)\s*s', content)
            seconds = int(seconds_match.group(1)) if seconds_match else 0

            audio_data = {
                'url': '',
                'seconds': seconds,
                'ptt': 'voz' in content.lower(),
                'mimetype': 'audio/ogg',
                'fileLength': 0,
                'waveform': ''
            }

        if not audio_data:
            return None

        # Criar player moderno
        player = InstagramStyleAudioPlayer(audio_data)
        return player

    except Exception as e:
        print(f"❌ Erro ao criar player Instagram: {e}")
        return None


# =============================================================================
# 🎵 EXEMPLO DE USO NO CHAT_WIDGET.PY
# =============================================================================

def update_message_bubble_for_audio(message_bubble_class):
    """
    Função para atualizar MessageBubble com novo player de áudio
    Adicione esta atualização no seu chat_widget.py
    """

    # Substituir método _create_media_preview
    def _create_media_preview_modern(self):
        """ATUALIZADO: Preview moderno para mensagens de mídia"""
        message_type = self.message_data.get('message_type', 'text')

        if message_type == 'audio':
            # Usar novo player Instagram style
            audio_player = create_instagram_style_audio_preview(self.message_data)
            if audio_player:
                preview_widget = QWidget()
                preview_layout = QVBoxLayout(preview_widget)
                preview_layout.setContentsMargins(0, 8, 0, 0)
                preview_layout.addWidget(audio_player)
                return preview_widget
            else:
                # Fallback para preview simples
                return self._create_simple_audio_preview()

        # Para outros tipos de mídia, manter implementação original
        return self._create_original_media_preview()

    # Substituir método no MessageBubble
    message_bubble_class._create_media_preview = _create_media_preview_modern

    return message_bubble_class


# =============================================================================
# 🎨 INSTRUÇÕES DE INTEGRAÇÃO
# =============================================================================

"""
COMO INTEGRAR NO SEU PROJETO:

1. SUBSTITUIR AudioPlayerWidget no chat_widget.py:
   - Trocar AudioPlayerWidget por InstagramStyleAudioPlayer
   - Usar create_instagram_style_audio_preview() para criar players

2. ATUALIZAR MessageBubble._create_media_preview():
   ```python
   if message_type == 'audio':
       audio_player = create_instagram_style_audio_preview(self.message_data)
       if audio_player:
           preview_widget = QWidget()
           preview_layout = QVBoxLayout(preview_widget)
           preview_layout.setContentsMargins(0, 8, 0, 0)
           preview_layout.addWidget(audio_player)
           return preview_widget
   ```

3. DEPENDÊNCIAS NECESSÁRIAS:
   pip install PyQt6
   pip install requests
   pip install pydub
   pip install SpeechRecognition
   pip install openai-whisper

4. RECURSOS INCLUÍDOS:
   ✅ Visual moderno estilo Instagram
   ✅ Waveform personalizada interativa
   ✅ Player funcional com controles
   ✅ Download otimizado de áudio
   ✅ Transcrição com Whisper/Google
   ✅ Animações suaves
   ✅ Interface responsiva
   ✅ Cleanup automático de recursos

5. FUNCIONALIDADES:
   • Clique no botão verde para reproduzir
   • Clique na waveform para buscar posição
   • Botão rosa para transcrever
   • Status visual em tempo real
   • Suporte a mensagens de voz e áudio
   • Conversão automática de formatos
   • Interface moderna e intuitiva

O player agora tem visual profissional similar ao Instagram!
"""
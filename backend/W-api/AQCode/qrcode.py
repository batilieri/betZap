import sys
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                             QHBoxLayout, QWidget, QPushButton, QLabel,
                             QLineEdit, QTextEdit, QProgressBar, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QFont
import qrcode
import io
import base64


class WhatsAppQRThread(QThread):
    """Thread para operações da API WhatsApp"""
    qr_received = pyqtSignal(object)
    status_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    instance_updated = pyqtSignal(str)

    def __init__(self, api_url, api_token, instance_id=None):
        super().__init__()
        self.api_url = api_url
        self.api_token = api_token
        self.session_id = instance_id
        self.running = False

    def run(self):
        """Executa o processo de conexão"""
        self.running = True
        try:
            # 1. Solicitar QR Code
            self.status_updated.emit("Solicitando QR Code...")
            qr_data = self.get_qr_code()

            if qr_data:
                self.qr_received.emit(qr_data)
                self.status_updated.emit("QR Code gerado! Escaneie com seu celular.")

                # 2. Verificar status da conexão (polling)
                while self.running:
                    status = self.check_connection_status()

                    if status == "connected":
                        self.status_updated.emit("✅ Conectado com sucesso!")
                        break
                    elif status == "disconnected":
                        self.status_updated.emit("❌ Desconectado")
                        break
                    elif status == "error":
                        self.status_updated.emit("❌ Erro na verificação de status")
                        break
                    elif status == "connecting":
                        self.status_updated.emit("🔄 Conectando...")

                    self.msleep(3000)  # Verifica a cada 3 segundos

        except Exception as e:
            self.error_occurred.emit(f"Erro: {str(e)}")

    def get_qr_code(self):
        """Solicita QR Code da API W-API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}'
            }

            # Instance ID é obrigatório na W-API
            if not self.session_id:
                self.error_occurred.emit("Instance ID é obrigatório para a W-API")
                return None

            # Endpoint correto da W-API
            params = {
                'instanceId': self.session_id,
                'syncContacts': 'disable',
                'image': 'enable'
            }

            self.status_updated.emit("🔄 Solicitando QR Code...")

            response = requests.get(
                f"{self.api_url}/v1/instance/qr-code",
                headers=headers,
                params=params,
                timeout=30
            )

            # Debug: Log da resposta
            self.status_updated.emit(f"📡 Status HTTP: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Tamanho (bytes): {len(response.content)}")

            # Verificar tipo de conteúdo
            content_type = response.headers.get('Content-Type', '')

            if response.status_code != 200:
                self.error_occurred.emit(
                    f"Falha ao gerar QR code. Código: {response.status_code}\nResposta: {response.text[:200]}")
                return None

            if 'application/json' in content_type:
                # É um JSON
                try:
                    data = response.json()

                    if data.get("error"):
                        error_msg = data.get('message', 'Erro desconhecido da API')
                        self.error_occurred.emit(f"API retornou erro: {error_msg}")
                        return None

                    qrcode_data = data.get("qrcode")
                    if not qrcode_data:
                        self.error_occurred.emit(f"QR code não disponível\nResposta: {data}")
                        return None

                    # Salvar instanceId se retornado
                    if 'instanceId' in data:
                        self.session_id = data['instanceId']
                        self.instance_updated.emit(self.session_id)

                    return qrcode_data

                except ValueError as json_error:
                    self.error_occurred.emit(
                        f"Resposta inválida da API. Não é um JSON válido.\nResposta: {response.text[:200]}")
                    return None

            elif 'image/' in content_type:
                # É uma imagem binária
                self.status_updated.emit("📷 Recebendo imagem QR Code diretamente...")
                return response.content  # Retorna dados binários da imagem

            else:
                self.error_occurred.emit(f"Tipo de resposta inesperado: {content_type}")
                return None

        except requests.exceptions.Timeout:
            self.error_occurred.emit("⏱️ Timeout - API demorou para responder")
            return None
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("🌐 Erro de conexão - verifique sua internet")
            return None
        except requests.RequestException as e:
            self.error_occurred.emit(f"🔌 Erro de requisição: {str(e)}")
            return None
        except Exception as e:
            self.error_occurred.emit(f"❌ Erro inesperado: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def check_connection_status(self):
        """Verifica status da conexão W-API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}'
            }

            # Instance ID é obrigatório
            if not self.session_id:
                return 'error'

            params = {
                'instanceId': self.session_id
            }

            response = requests.get(
                 f"{self.api_url}/v1/instance/status-instance",
                headers=headers,
                params=params,
                timeout=15
            )

            # Verificar tipo de conteúdo
            content_type = response.headers.get('Content-Type', '')

            if response.status_code == 200:
                if 'application/json' in content_type:
                    try:
                        data = response.json()

                        if data.get("error"):
                            return 'error'

                        # Status possíveis da W-API: 'connected', 'disconnected', 'connecting'
                        status = data.get('status', 'waiting')
                        return status

                    except ValueError:
                        # Se não conseguir fazer parse do JSON
                        return 'error'
                else:
                    return 'error'
            else:
                return 'error'

        except requests.exceptions.Timeout:
            return 'error'
        except requests.RequestException:
            return 'error'
        except Exception:
            return 'error'

    def stop(self):
        """Para o thread"""
        self.running = False


class WhatsAppQRWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.qr_thread = None
        self.init_ui()

    def init_ui(self):
        """Inicializa interface do usuário"""
        self.setWindowTitle("WhatsApp QR Code Connection")
        self.setGeometry(100, 100, 600, 700)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QVBoxLayout(central_widget)

        # Título
        title = QLabel("Conexão WhatsApp via QR Code")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Configurações da API
        config_layout = QVBoxLayout()

        # URL da API
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL da API:"))
        self.url_input = QLineEdit()
        self.url_input.setText("https://api.w-api.app")  # URL oficial da W-API
        self.url_input.setPlaceholderText("Ex: https://api.w-api.app")
        url_layout.addWidget(self.url_input)
        config_layout.addLayout(url_layout)

        # Token da API
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("Token API:"))
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Seu token da W-API")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        token_layout.addWidget(self.token_input)

        # Botão para mostrar/ocultar token
        self.show_token_btn = QPushButton("👁")
        self.show_token_btn.setMaximumWidth(30)
        self.show_token_btn.setCheckable(True)
        self.show_token_btn.clicked.connect(self.toggle_token_visibility)
        token_layout.addWidget(self.show_token_btn)
        config_layout.addLayout(token_layout)

        # Instance ID (obrigatório)
        instance_layout = QHBoxLayout()
        instance_layout.addWidget(QLabel("Instance ID*:"))
        self.instance_input = QLineEdit()
        self.instance_input.setPlaceholderText("Instance ID é obrigatório (ex: T34398-VYR3QD-MS29SL)")
        instance_layout.addWidget(self.instance_input)
        config_layout.addLayout(instance_layout)

        layout.addLayout(config_layout)

        # Botões de controle
        button_layout = QHBoxLayout()

        # Botão testar conexão
        self.test_btn = QPushButton("🔧 Testar API")
        self.test_btn.clicked.connect(self.test_api_connection)
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(self.test_btn)

        self.connect_btn = QPushButton("🔗 Conectar")
        self.connect_btn.clicked.connect(self.start_connection)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
        """)
        button_layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("❌ Desconectar")
        self.disconnect_btn.clicked.connect(self.stop_connection)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC143C;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B22222;
            }
        """)
        button_layout.addWidget(self.disconnect_btn)

        layout.addLayout(button_layout)

        # Área do QR Code
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setMinimumHeight(250)
        self.qr_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #25D366;
                border-radius: 10px;
                background-color: #f0f0f0;
            }
        """)
        self.qr_label.setText("QR Code aparecerá aqui")
        layout.addWidget(self.qr_label)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel("Pronto para conectar")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #1976d2;
            }
        """)
        layout.addWidget(self.status_label)

        # Instance ID atual
        self.current_instance_label = QLabel("Instance ID: Não conectado")
        self.current_instance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_instance_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                padding: 5px;
                border-radius: 3px;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.current_instance_label)

        # Log de atividades
        log_label = QLabel("Log de Atividades:")
        log_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # Adicionar entrada inicial ao log
        self.add_log("Aplicação iniciada")
        self.add_log("⚠️ IMPORTANTE: Instance ID é obrigatório para W-API")
        self.add_log("💡 Crie uma instância no dashboard da W-API primeiro")

    def test_api_connection(self):
        """Testa a conexão com a API"""
        api_url = self.url_input.text().strip()
        api_token = self.token_input.text().strip()
        instance_id = self.instance_input.text().strip()

        if not api_url or not api_token:
            QMessageBox.warning(self, "Aviso", "Por favor, preencha URL e Token da API")
            return

        if not instance_id:
            QMessageBox.warning(self, "Aviso", "Instance ID é obrigatório para testar a API W-API")
            return

        self.test_btn.setEnabled(False)
        self.test_btn.setText("🔄 Testando...")
        self.add_log("Testando conexão com a API...")

        try:
            headers = {
                'Authorization': f'Bearer {api_token}'
            }

            # Testar com endpoint de status usando Instance ID
            response = requests.get(
                   f"{api_url}/v1/instance/status-instance",
                headers=headers,
                params={'instanceId': instance_id},
                timeout=10
            )

            self.add_log(f"Status da resposta: {response.status_code}")
            self.add_log(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            self.add_log(f"Conteúdo: {response.text[:100]}...")

            # Verificar tipo de conteúdo
            content_type = response.headers.get('Content-Type', '')

            if response.status_code == 200:
                if 'application/json' in content_type:
                    try:
                        data = response.json()

                        if data.get("error"):
                            error_msg = data.get('message', 'Erro desconhecido')
                            QMessageBox.warning(self, "⚠️ Aviso da API", f"API retornou: {error_msg}")
                            self.add_log(f"⚠️ API retornou erro: {error_msg}")
                        else:
                            status = data.get('status', 'N/A')
                            QMessageBox.information(self, "✅ Sucesso",
                                                    f"Conexão estabelecida!\n\nStatus da instância: {status}")
                            self.add_log(f"✅ API funcionando - Status: {status}")
                    except ValueError:
                        QMessageBox.warning(self, "⚠️ Aviso", "API respondeu, mas retornou dados inválidos")
                        self.add_log("⚠️ Resposta da API não é JSON válido")
                else:
                    QMessageBox.warning(self, "⚠️ Aviso", f"Tipo de resposta inesperado: {content_type}")
                    self.add_log(f"⚠️ Content-Type inesperado: {content_type}")
            elif response.status_code == 401:
                QMessageBox.critical(self, "❌ Erro", "Token inválido ou expirado")
                self.add_log("❌ Erro de autenticação")
            elif response.status_code == 403:
                QMessageBox.critical(self, "❌ Erro", "Acesso negado - verifique permissões")
                self.add_log("❌ Acesso negado")
            else:
                QMessageBox.critical(self, "❌ Erro", f"API retornou erro: {response.status_code}")
                self.add_log(f"❌ Erro HTTP: {response.status_code}")

        except requests.exceptions.Timeout:
            QMessageBox.critical(self, "❌ Erro", "Timeout - API demorou para responder")
            self.add_log("❌ Timeout na API")
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "❌ Erro", "Erro de conexão - verifique URL e internet")
            self.add_log("❌ Erro de conexão")
        except Exception as e:
            QMessageBox.critical(self, "❌ Erro", f"Erro inesperado: {str(e)}")
            self.add_log(f"❌ Erro: {str(e)}")
        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText("🔧 Testar API")

    def toggle_token_visibility(self):
        """Alterna visibilidade do token"""
        if self.show_token_btn.isChecked():
            self.token_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_token_btn.setText("🙈")
        else:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_token_btn.setText("👁")

    def add_log(self, message):
        """Adiciona mensagem ao log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def start_connection(self):
        """Inicia processo de conexão"""
        api_url = self.url_input.text().strip()
        api_token = self.token_input.text().strip()
        instance_id = self.instance_input.text().strip()

        # Validações
        if not api_url or not api_token:
            QMessageBox.warning(self, "Aviso", "Por favor, preencha URL e Token da API")
            return

        # Instance ID é OBRIGATÓRIO para W-API
        if not instance_id:
            QMessageBox.warning(self, "Aviso",
                                "Instance ID é obrigatório para a W-API.\n\nCrie uma instância no dashboard da W-API primeiro.")
            return

        # Validar formato da URL
        if not api_url.startswith(('http://', 'https://')):
            QMessageBox.warning(self, "Aviso", "URL deve começar com http:// ou https://")
            return

        # Remover barra final se existir
        api_url = api_url.rstrip('/')

        # Validar token (deve ter pelo menos 10 caracteres)
        if len(api_token) < 10:
            QMessageBox.warning(self, "Aviso", "Token parece muito curto. Verifique se está correto.")
            return

        # Configurar interface
        self.connect_btn.setEnabled(False)
        self.test_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminado

        # Iniciar thread
        self.qr_thread = WhatsAppQRThread(api_url, api_token, instance_id)
        self.qr_thread.qr_received.connect(self.display_qr_code)
        self.qr_thread.status_updated.connect(self.update_status)
        self.qr_thread.error_occurred.connect(self.handle_error)
        self.qr_thread.instance_updated.connect(self.update_instance_id)
        self.qr_thread.start()

        self.add_log(f"Iniciando conexão com Instance ID: {instance_id}")

    def display_qr_code(self, qr_data):
        """Exibe QR Code na interface"""
        try:
            pixmap = QPixmap()

            if isinstance(qr_data, bytes):
                # Dados binários de imagem (resposta direta da API)
                pixmap.loadFromData(qr_data)
                self.add_log("QR Code carregado como imagem binária")

            elif isinstance(qr_data, str) and qr_data.startswith('data:image/png;base64,'):
                # Extrair dados base64 da resposta da API
                base64_data = qr_data.split(',')[1]
                image_data = base64.b64decode(base64_data)
                pixmap.loadFromData(image_data)
                self.add_log("QR Code carregado como base64")

            elif isinstance(qr_data, str):
                # Gerar QR Code tradicional (fallback para texto simples)
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=8,
                    border=4,
                )
                qr.add_data(qr_data)
                qr.make(fit=True)

                # Criar imagem
                img = qr.make_image(fill_color="black", back_color="white")

                # Converter para QPixmap
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()

                pixmap.loadFromData(img_byte_arr)
                self.add_log("QR Code gerado localmente")

            if pixmap.isNull():
                self.handle_error("Erro ao carregar imagem do QR Code")
                return

            # Redimensionar para caber na interface
            scaled_pixmap = pixmap.scaled(
                400, 400,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.qr_label.setPixmap(scaled_pixmap)
            self.add_log("QR Code exibido com sucesso")

        except Exception as e:
            self.handle_error(f"Erro ao processar QR Code: {str(e)}")
            import traceback
            traceback.print_exc()

    def update_instance_id(self, instance_id):
        """Atualiza o Instance ID exibido"""
        self.current_instance_label.setText(f"Instance ID: {instance_id}")
        self.add_log(f"Instance ID: {instance_id}")

    def update_status(self, status):
        """Atualiza status da conexão"""
        self.status_label.setText(status)
        self.add_log(status)

        if "Conectado com sucesso" in status or "connected" in status.lower():
            self.progress_bar.setVisible(False)
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #e8f5e8;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #4caf50;
                    color: #2e7d32;
                    font-weight: bold;
                }
            """)
        elif "disconnected" in status.lower() or "Tempo limite" in status or "❌" in status:
            self.progress_bar.setVisible(False)
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #ffebee;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #f44336;
                    color: #c62828;
                    font-weight: bold;
                }
            """)
        elif "connecting" in status.lower() or "Solicitando" in status:
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3e0;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #ff9800;
                    color: #e65100;
                    font-weight: bold;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #e3f2fd;
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #1976d2;
                }
            """)

    def handle_error(self, error_msg):
        """Trata erros"""
        self.add_log(f"ERRO: {error_msg}")
        self.status_label.setText(f"❌ {error_msg}")
        self.progress_bar.setVisible(False)

        # Criar mensagem de erro mais detalhada
        detailed_msg = f"Erro: {error_msg}\n\n"

        if "Token inválido" in error_msg or "401" in error_msg:
            detailed_msg += "💡 Soluções:\n• Verifique se o token está correto\n• Confirme se o token não expirou\n• Teste a conexão primeiro"
        elif "Erro de conexão" in error_msg or "ConnectionError" in error_msg:
            detailed_msg += "💡 Soluções:\n• Verifique sua conexão com internet\n• Confirme se a URL está correta\n• Tente novamente em alguns minutos"
        elif "Timeout" in error_msg:
            detailed_msg += "💡 Soluções:\n• API está demorando para responder\n• Verifique sua conexão\n• Tente novamente"
        elif "Resposta inválida" in error_msg:
            detailed_msg += "💡 Soluções:\n• API pode estar fora do ar\n• Verifique se a URL está correta\n• Teste a conexão primeiro"
        else:
            detailed_msg += "💡 Soluções:\n• Use o botão 'Testar API' primeiro\n• Verifique URL e Token\n• Consulte o log para mais detalhes"

        QMessageBox.critical(self, "Erro de Conexão", detailed_msg)
        self.stop_connection()

    def stop_connection(self):
        """Para a conexão"""
        if self.qr_thread:
            self.qr_thread.stop()
            self.qr_thread.wait()

        # Resetar interface
        self.connect_btn.setEnabled(True)
        self.test_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.qr_label.clear()
        self.qr_label.setText("QR Code aparecerá aqui")
        self.status_label.setText("Desconectado")
        self.current_instance_label.setText("Instance ID: Não conectado")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #1976d2;
            }
        """)

        self.add_log("Conexão interrompida")

    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        if self.qr_thread:
            self.qr_thread.stop()
            self.qr_thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)

    # Configurar estilo da aplicação
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QLineEdit {
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 12px;
        }
        QLineEdit:focus {
            border-color: #25D366;
        }
        QLabel {
            font-size: 12px;
        }
    """)

    window = WhatsAppQRWidget()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
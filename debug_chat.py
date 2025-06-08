#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Versão de debug para identificar problemas com mensagens que desaparecem
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QTimer


class SimpleTestWindow(QMainWindow):
    """Janela de teste simples para debug"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Debug - Teste de Mensagens")
        self.setGeometry(200, 200, 600, 400)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)

        # Área de controles
        controls_layout = QVBoxLayout()

        # Botão para adicionar mensagem
        self.add_btn = QPushButton("Adicionar Mensagem de Teste")
        self.add_btn.clicked.connect(self.add_test_message)
        controls_layout.addWidget(self.add_btn)

        # Botão para limpar
        self.clear_btn = QPushButton("Limpar Mensagens")
        self.clear_btn.clicked.connect(self.clear_messages)
        controls_layout.addWidget(self.clear_btn)

        # Contador
        self.counter_label = QLabel("Mensagens: 0")
        controls_layout.addWidget(self.counter_label)

        main_layout.addLayout(controls_layout)

        # Área de mensagens (simples)
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setSpacing(5)

        # Widget container para as mensagens
        self.messages_widget = QWidget()
        self.messages_widget.setLayout(self.messages_layout)
        self.messages_widget.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")

        main_layout.addWidget(self.messages_widget, 1)

        self.message_count = 0

    def add_test_message(self):
        """Adiciona uma mensagem de teste"""
        self.message_count += 1

        # Criar mensagem simples
        message_label = QLabel(f"Mensagem de teste #{self.message_count}")
        message_label.setStyleSheet("""
            QLabel {
                background-color: white;
                padding: 10px;
                border-radius: 10px;
                margin: 2px;
                border: 1px solid #ddd;
            }
        """)

        # Adicionar ao layout
        self.messages_layout.addWidget(message_label)

        # Atualizar contador
        self.counter_label.setText(f"Mensagens: {self.message_count}")

        # Log
        print(f"✅ Mensagem #{self.message_count} adicionada")
        print(f"   Widgets no layout: {self.messages_layout.count()}")

        # Forçar atualização
        self.messages_widget.updateGeometry()
        QApplication.processEvents()

    def clear_messages(self):
        """Limpa todas as mensagens"""
        print(f"🧹 Limpando {self.messages_layout.count()} widgets...")

        # Remover todos os widgets
        while self.messages_layout.count() > 0:
            child = self.messages_layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                print(f"   Removendo: {widget}")
                widget.deleteLater()

        # Resetar contador
        self.message_count = 0
        self.counter_label.setText("Mensagens: 0")

        # Processar eventos para garantir remoção
        QApplication.processEvents()

        print(f"✅ Limpeza concluída. Widgets restantes: {self.messages_layout.count()}")


def test_simple_messages():
    """Teste simples para verificar se mensagens ficam visíveis"""
    app = QApplication(sys.argv)

    window = SimpleTestWindow()
    window.show()

    print("🧪 TESTE DE DEBUG INICIADO")
    print("1. Clique em 'Adicionar Mensagem de Teste'")
    print("2. Verifique se as mensagens ficam visíveis")
    print("3. Use 'Limpar Mensagens' para testar remoção")

    sys.exit(app.exec())


if __name__ == '__main__':
    test_simple_messages()
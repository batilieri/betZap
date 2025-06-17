#!/usr/bin/env python3
"""
Aplicação Web para Chat WhatsApp integrada com Banco de Dados
Sistema completo de chat em tempo real
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua-chave-secreta-super-segura-2024'
socketio = SocketIO(app, cors_allowed_origins="*")


# Simular banco de dados em memória (substitua pela integração real)
class ChatDatabase:
    def __init__(self):
        self.chats = []
        self.contacts = []
        self.messages = []
        self._init_sample_data()

    def _init_sample_data(self):
        """Inicializa dados de exemplo"""
        self.contacts = [
            {
                'id': '1',
                'name': 'Liam Santos',
                'phone': '5569999267344',
                'profile_picture': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face',
                'last_message': 'Ótimo! Nos vemos lá então. Até mais tarde!',
                'last_message_time': datetime.now() - timedelta(minutes=5),
                'unread_count': 0,
                'is_online': True
            },
            {
                'id': '2',
                'name': 'Maria Silva',
                'phone': '5569988776655',
                'profile_picture': 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400&h=400&fit=crop&crop=face',
                'last_message': 'Obrigada pela ajuda!',
                'last_message_time': datetime.now() - timedelta(hours=2),
                'unread_count': 2,
                'is_online': False
            },
            {
                'id': '3',
                'name': 'João Pedro',
                'phone': '5569987654321',
                'profile_picture': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop&crop=face',
                'last_message': 'Vamos marcar para amanhã?',
                'last_message_time': datetime.now() - timedelta(hours=5),
                'unread_count': 1,
                'is_online': True
            }
        ]

        self.messages = [
            {
                'id': '1',
                'contact_id': '1',
                'content': 'Oi, Sophia! Tudo bem? Estou te escrevendo para saber se você está livre para jantar hoje à noite.',
                'is_from_me': False,
                'timestamp': datetime.now() - timedelta(minutes=30),
                'message_type': 'text',
                'status': 'delivered'
            },
            {
                'id': '2',
                'contact_id': '1',
                'content': 'Oi, Liam! Que ótima ideia! Sim, estou livre. Que tipo de cozinha é?',
                'is_from_me': True,
                'timestamp': datetime.now() - timedelta(minutes=28),
                'message_type': 'text',
                'status': 'read'
            },
            {
                'id': '3',
                'contact_id': '1',
                'content': 'É um restaurante italiano com um toque moderno. As avaliações são excelentes!',
                'is_from_me': False,
                'timestamp': datetime.now() - timedelta(minutes=25),
                'message_type': 'text',
                'status': 'delivered'
            },
            {
                'id': '4',
                'contact_id': '1',
                'content': 'Adoro comida italiana! Que horas você estava pensando?',
                'is_from_me': True,
                'timestamp': datetime.now() - timedelta(minutes=22),
                'message_type': 'text',
                'status': 'read'
            },
            {
                'id': '5',
                'contact_id': '1',
                'content': 'Podemos nos encontrar às 20h? Assim, temos tempo para aproveitar a noite.',
                'is_from_me': False,
                'timestamp': datetime.now() - timedelta(minutes=20),
                'message_type': 'text',
                'status': 'delivered'
            },
            {
                'id': '6',
                'contact_id': '1',
                'content': 'Perfeito! Às 20h está ótimo. Mal posso esperar para experimentar esse novo lugar.',
                'is_from_me': True,
                'timestamp': datetime.now() - timedelta(minutes=18),
                'message_type': 'text',
                'status': 'read'
            },
            {
                'id': '7',
                'contact_id': '1',
                'content': 'Ótimo! Nos vemos lá então. Até mais tarde!',
                'is_from_me': False,
                'timestamp': datetime.now() - timedelta(minutes=15),
                'message_type': 'text',
                'status': 'delivered'
            },
            {
                'id': '8',
                'contact_id': '1',
                'content': 'Até mais, Liam! Estou ansiosa!',
                'is_from_me': True,
                'timestamp': datetime.now() - timedelta(minutes=10),
                'message_type': 'text',
                'status': 'read'
            }
        ]

    def get_contacts(self):
        """Retorna lista de contatos ordenada por última mensagem"""
        return sorted(self.contacts, key=lambda x: x['last_message_time'], reverse=True)

    def get_contact_by_id(self, contact_id):
        """Busca contato por ID"""
        return next((c for c in self.contacts if c['id'] == contact_id), None)

    def get_messages_by_contact(self, contact_id):
        """Retorna mensagens de um contato específico"""
        return [m for m in self.messages if m['contact_id'] == contact_id]

    def add_message(self, contact_id, content, is_from_me=True):
        """Adiciona nova mensagem"""
        message = {
            'id': str(len(self.messages) + 1),
            'contact_id': contact_id,
            'content': content,
            'is_from_me': is_from_me,
            'timestamp': datetime.now(),
            'message_type': 'text',
            'status': 'sent' if is_from_me else 'received'
        }
        self.messages.append(message)

        # Atualizar último contato
        contact = self.get_contact_by_id(contact_id)
        if contact:
            contact['last_message'] = content
            contact['last_message_time'] = datetime.now()
            if not is_from_me:
                contact['unread_count'] += 1

        return message


# Instância do banco
db = ChatDatabase()


@app.route('/')
def index():
    """Página principal - redireciona para o chat"""
    return redirect(url_for('chat_page'))


@app.route('/chat')
def chat_page():
    """Página principal do chat"""
    contacts = db.get_contacts()
    return render_template('chat.html', contacts=contacts)


@app.route('/chat/<contact_id>')
def chat_with_contact(contact_id):
    """Chat com contato específico"""
    contact = db.get_contact_by_id(contact_id)
    if not contact:
        return redirect(url_for('chat_page'))

    messages = db.get_messages_by_contact(contact_id)
    contacts = db.get_contacts()

    # Marcar mensagens como lidas
    contact['unread_count'] = 0

    return render_template('chat.html',
                           contacts=contacts,
                           active_contact=contact,
                           messages=messages)


@app.route('/api/contacts')
def api_contacts():
    """API para listar contatos"""
    contacts = db.get_contacts()
    return jsonify({
        'success': True,
        'contacts': [
            {
                'id': c['id'],
                'name': c['name'],
                'profile_picture': c['profile_picture'],
                'last_message': c['last_message'],
                'last_message_time': c['last_message_time'].isoformat(),
                'unread_count': c['unread_count'],
                'is_online': c['is_online']
            }
            for c in contacts
        ]
    })


@app.route('/api/messages/<contact_id>')
def api_messages(contact_id):
    """API para buscar mensagens de um contato"""
    contact = db.get_contact_by_id(contact_id)
    if not contact:
        return jsonify({'success': False, 'error': 'Contato não encontrado'}), 404

    messages = db.get_messages_by_contact(contact_id)
    return jsonify({
        'success': True,
        'contact': {
            'id': contact['id'],
            'name': contact['name'],
            'profile_picture': contact['profile_picture'],
            'is_online': contact['is_online']
        },
        'messages': [
            {
                'id': m['id'],
                'content': m['content'],
                'is_from_me': m['is_from_me'],
                'timestamp': m['timestamp'].isoformat(),
                'message_type': m['message_type'],
                'status': m['status']
            }
            for m in messages
        ]
    })


@app.route('/api/send_message', methods=['POST'])
def api_send_message():
    """API para enviar mensagem"""
    data = request.get_json()

    contact_id = data.get('contact_id')
    content = data.get('content')

    if not contact_id or not content:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400

    contact = db.get_contact_by_id(contact_id)
    if not contact:
        return jsonify({'success': False, 'error': 'Contato não encontrado'}), 404

    # Adicionar mensagem
    message = db.add_message(contact_id, content, is_from_me=True)

    # Emitir via WebSocket
    socketio.emit('new_message', {
        'contact_id': contact_id,
        'message': {
            'id': message['id'],
            'content': message['content'],
            'is_from_me': message['is_from_me'],
            'timestamp': message['timestamp'].isoformat(),
            'message_type': message['message_type'],
            'status': message['status']
        }
    })

    return jsonify({
        'success': True,
        'message': {
            'id': message['id'],
            'content': message['content'],
            'is_from_me': message['is_from_me'],
            'timestamp': message['timestamp'].isoformat(),
            'message_type': message['message_type'],
            'status': message['status']
        }
    })


# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    logger.info(f"Cliente conectado: {request.sid}")
    emit('connected', {'message': 'Conectado ao chat'})


@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    logger.info(f"Cliente desconectado: {request.sid}")


@socketio.on('join_chat')
def handle_join_chat(data):
    """Cliente entrou em um chat específico"""
    contact_id = data.get('contact_id')
    if contact_id:
        join_room(f"chat_{contact_id}")
        logger.info(f"Cliente {request.sid} entrou no chat {contact_id}")


@socketio.on('leave_chat')
def handle_leave_chat(data):
    """Cliente saiu de um chat específico"""
    contact_id = data.get('contact_id')
    if contact_id:
        leave_room(f"chat_{contact_id}")
        logger.info(f"Cliente {request.sid} saiu do chat {contact_id}")


@socketio.on('send_message')
def handle_send_message(data):
    """Enviar mensagem via WebSocket"""
    contact_id = data.get('contact_id')
    content = data.get('content')

    if not contact_id or not content:
        emit('error', {'message': 'Dados inválidos'})
        return

    contact = db.get_contact_by_id(contact_id)
    if not contact:
        emit('error', {'message': 'Contato não encontrado'})
        return

    # Adicionar mensagem
    message = db.add_message(contact_id, content, is_from_me=True)

    # Emitir para todos no chat
    socketio.emit('new_message', {
        'contact_id': contact_id,
        'message': {
            'id': message['id'],
            'content': message['content'],
            'is_from_me': message['is_from_me'],
            'timestamp': message['timestamp'].isoformat(),
            'message_type': message['message_type'],
            'status': message['status']
        }
    }, room=f"chat_{contact_id}")


@app.errorhandler(404)
def not_found(error):
    """Página de erro 404"""
    return render_template('error.html',
                           error_code=404,
                           error_message="Página não encontrada"), 404


@app.errorhandler(500)
def internal_error(error):
    """Página de erro 500"""
    return render_template('error.html',
                           error_code=500,
                           error_message="Erro interno do servidor"), 500


if __name__ == '__main__':
    # Verificar se pasta templates existe
    if not os.path.exists('templates'):
        os.makedirs('templates')
        logger.warning("⚠️ Pasta 'templates' criada. Adicione os arquivos HTML.")

    if not os.path.exists('static'):
        os.makedirs('static')
        logger.warning("⚠️ Pasta 'static' criada. Adicione os arquivos CSS/JS.")

    logger.info("🚀 Iniciando servidor Flask...")
    logger.info("📱 Acesse: http://localhost:5000")

    # Executar com SocketIO
    socketio.run(app,
                 host='0.0.0.0',
                 port=5000,
                 debug=True,
                 allow_unsafe_werkzeug=True)
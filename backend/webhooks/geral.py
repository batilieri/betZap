import requests
import json

# Configurações básicas
BASE_URL = "https://api.w-api.app/v1/webhook"
INSTANCE_ID = "sua_instancia_aqui"  # Substituir pela sua instância
TOKEN = "seu_token_aqui"  # Substituir pelo seu token

# Headers padrão
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}


# ================================================================
# 1. WEBHOOK DE CONEXÃO (Ao Conectar)
# ================================================================

def configurar_webhook_conexao():
    """
    Configura webhook para ser notificado quando WhatsApp conectar
    Útil para: Saber quando QR Code foi escaneado ou código pareado
    """
    url = f"{BASE_URL}/update-webhook-connected"
    params = {"instanceId": INSTANCE_ID}

    data = {
        "value": "https://seusite.com/webhook/conectado"
    }

    try:
        response = requests.put(url, headers=headers, params=params, json=data)

        if response.status_code == 200:
            print("✅ Webhook de conexão configurado com sucesso!")
            print(f"Resposta: {response.json()}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")


# ================================================================
# 2. WEBHOOK DE DESCONEXÃO (Ao Desconectar)
# ================================================================

def configurar_webhook_desconexao():
    """
    Configura webhook para ser notificado quando WhatsApp desconectar
    Útil para: Saber quando conexão foi perdida
    """
    url = f"{BASE_URL}/update-webhook-disconnected"
    params = {"instanceId": INSTANCE_ID}

    data = {
        "value": "https://seusite.com/webhook/desconectado"
    }

    try:
        response = requests.put(url, headers=headers, params=params, json=data)

        if response.status_code == 200:
            print("✅ Webhook de desconexão configurado com sucesso!")
            print(f"Resposta: {response.json()}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")


# ================================================================
# 3. WEBHOOK DE ENTREGA (Ao Enviar)
# ================================================================

def configurar_webhook_entrega():
    """
    Configura webhook para receber status de mensagens enviadas
    Útil para: Confirmar se mensagens foram entregues
    """
    url = f"{BASE_URL}/update-webhook-delivery"
    params = {"instanceId": INSTANCE_ID}

    data = {
        "value": "https://seusite.com/webhook/entrega"
    }

    try:
        response = requests.put(url, headers=headers, params=params, json=data)

        if response.status_code == 200:
            print("✅ Webhook de entrega configurado com sucesso!")
            print(f"Resposta: {response.json()}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")


# ================================================================
# 4. WEBHOOK DE RECEBIMENTO (Ao Receber)
# ================================================================

def configurar_webhook_recebimento():
    """
    Configura webhook para receber mensagens
    Útil para: Receber todas as mensagens em tempo real
    """
    url = f"{BASE_URL}/update-webhook-received"
    params = {"instanceId": INSTANCE_ID}

    data = {
        "value": "https://seusite.com/webhook/mensagens"
    }

    try:
        response = requests.put(url, headers=headers, params=params, json=data)

        if response.status_code == 200:
            print("✅ Webhook de recebimento configurado com sucesso!")
            print(f"Resposta: {response.json()}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")


# ================================================================
# 5. WEBHOOK DE STATUS DE MENSAGEM
# ================================================================

def configurar_webhook_status_mensagem():
    """
    Configura webhook para acompanhar status das mensagens
    Útil para: Saber se mensagem foi visualizada, entregue, etc.
    """
    url = f"{BASE_URL}/update-webhook-message-status"
    params = {"instanceId": INSTANCE_ID}

    data = {
        "value": "https://seusite.com/webhook/status-mensagem"
    }

    try:
        response = requests.put(url, headers=headers, params=params, json=data)

        if response.status_code == 200:
            print("✅ Webhook de status de mensagem configurado com sucesso!")
            print(f"Resposta: {response.json()}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")


# ================================================================
# 6. WEBHOOK DE PRESENÇA NO CHAT
# ================================================================

def configurar_webhook_presenca():
    """
    Configura webhook para receber status de presença
    Útil para: Saber quando contatos estão online, digitando, etc.
    """
    url = f"{BASE_URL}/update-webhook-chat-presence"
    params = {"instanceId": INSTANCE_ID}

    data = {
        "value": "https://seusite.com/webhook/presenca"
    }

    try:
        response = requests.put(url, headers=headers, params=params, json=data)

        if response.status_code == 200:
            print("✅ Webhook de presença configurado com sucesso!")
            print(f"Resposta: {response.json()}")
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")


# ================================================================
# FUNÇÃO PARA CONFIGURAR TODOS OS WEBHOOKS DE UMA VEZ
# ================================================================

def configurar_todos_webhooks():
    """
    Configura todos os webhooks de uma vez
    """
    print("🚀 Configurando todos os webhooks...\n")

    configurar_webhook_conexao()
    print("-" * 50)

    configurar_webhook_desconexao()
    print("-" * 50)

    configurar_webhook_entrega()
    print("-" * 50)

    configurar_webhook_recebimento()
    print("-" * 50)

    configurar_webhook_status_mensagem()
    print("-" * 50)

    configurar_webhook_presenca()
    print("-" * 50)

    print("✨ Configuração de webhooks concluída!")


# ================================================================
# EXEMPLO DE USO
# ================================================================

if __name__ == "__main__":
    # Exemplo 1: Configurar apenas webhook de mensagens recebidas
    print("=== CONFIGURANDO WEBHOOK DE MENSAGENS ===")
    configurar_webhook_recebimento()

    print("\n" + "=" * 60 + "\n")

    # Exemplo 2: Configurar todos os webhooks
    print("=== CONFIGURANDO TODOS OS WEBHOOKS ===")
    configurar_todos_webhooks()

# ================================================================
# EXEMPLO DE SERVIDOR FLASK PARA RECEBER OS WEBHOOKS
# ================================================================

"""
# Instalar Flask: pip install flask

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/conectado', methods=['POST'])
def webhook_conectado():
    data = request.json
    print("🟢 WhatsApp Conectado:", data)
    return jsonify({"status": "ok"})

@app.route('/webhook/desconectado', methods=['POST'])
def webhook_desconectado():
    data = request.json
    print("🔴 WhatsApp Desconectado:", data)
    return jsonify({"status": "ok"})

@app.route('/webhook/mensagens', methods=['POST'])
def webhook_mensagens():
    data = request.json
    print("💬 Nova Mensagem:", data)
    return jsonify({"status": "ok"})

@app.route('/webhook/entrega', methods=['POST'])
def webhook_entrega():
    data = request.json
    print("📤 Status de Entrega:", data)
    return jsonify({"status": "ok"})

@app.route('/webhook/status-mensagem', methods=['POST'])
def webhook_status():
    data = request.json
    print("📊 Status da Mensagem:", data)
    return jsonify({"status": "ok"})

@app.route('/webhook/presenca', methods=['POST'])
def webhook_presenca():
    data = request.json
    print("👁️ Status de Presença:", data)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
"""
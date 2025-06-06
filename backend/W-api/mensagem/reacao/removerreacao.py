import requests
import json

# Configurações
url = "https://api.w-api.app/v1/message/remove-reaction"
instance_id = "SUA_INSTANCE_ID"
token = "SEU_TOKEN"

# Parâmetros de query
params = {"instanceId": instance_id}

# Cabeçalhos
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Dados para remover a reação
payload = {
    "phone": "559199999999",
    "messageId": "3EB011ECFA6BD9C1C9053B",
    "delayMessage": 15  # Opcional
}

# Enviar a requisição
response = requests.post(url, headers=headers, params=params, data=json.dumps(payload))

# Verificar o resultado
if response.status_code == 200:
    print("✅ Reação removida com sucesso!")
    print("Resposta:", response.json())
else:
    print("❌ Erro ao remover reação:", response.status_code)
    print("Resposta:", response.text)

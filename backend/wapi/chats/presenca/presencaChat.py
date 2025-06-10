import requests
import json

# Configurações
url = "https://api.w-api.app/v1/chats/send-presence"
instance_id = "SUA_INSTANCE_ID"
token = "SEU_TOKEN_AQUI"

# Parâmetros de consulta
params = {
    "instanceId": instance_id
}

# Cabeçalhos
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Corpo da requisição
payload = {
    "phone": "559992249708",  # número de destino
    "presence": "composing",  # ou "recording"
    "delay": 15               # duração da presença, em segundos
}

# Envio da requisição POST
response = requests.post(url, headers=headers, params=params, data=json.dumps(payload))

# Tratamento da resposta
if response.status_code == 200:
    print("Resposta:", response.json())
else:
    print(f"Erro: {response.status_code}")
    print(response.text)

import requests
import json

# Configurações
url = "https://api.w-api.app/v1/message/send-reaction"
instance_id = "3B6XIW-ZTS923-GEAY6V"
token = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"

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
    "phone": "5569999267344",          # Número ou grupo destino
    "reaction": "😉",                 # Emoji de reação
    "messageId": "556999267344@s.whatsapp.net",  # ID da mensagem
    "delayMessage": 15               # Opcional, atraso no envio (em segundos)
}

# Envio da requisição POST
response = requests.post(url, headers=headers, params=params, data=json.dumps(payload))

# Tratamento da resposta
if response.status_code == 200:
    print("Reação enviada com sucesso!")
    print("Resposta:", response.json())
else:
    print(f"Erro: {response.status_code}")
    print(response.text)

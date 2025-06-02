import requests

BASE_URL = 'https://api.w-api.app/v1/webhook'
INSTANCE_ID = '3B6XIW-ZTS923-GEAY6V'
BEARER_TOKEN = 'Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF'

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {BEARER_TOKEN}'
}

# # Ao Conectar
# url = f'{BASE_URL}/update-webhook-connected?instanceId={INSTANCE_ID}'
# data = {"value": "https://webhook.site/bfc49dbf-c19a-438b-ab02-f4c698598280"}
#
# response = requests.put(url, json=data, headers=HEADERS)
# print(response.status_code, response.json())
#
# # Ao desconectar
# url = f'{BASE_URL}/update-webhook-disconnected?instanceId={INSTANCE_ID}'
# data = {"value": "https://webhook.site/bfc49dbf-c19a-438b-ab02-f4c698598280"}
#
# response = requests.put(url, json=data, headers=HEADERS)
# print(response.status_code, response.json())

# Ao enviar
url = f'{BASE_URL}/update-webhook-delivery?instanceId={INSTANCE_ID}'
data = {"value": "https://webhook.site/b843e182-e69e-4a23-86ca-3efc2efc506d"}

response = requests.put(url, json=data, headers=HEADERS)
print(response.status_code, response.json())

#  Ao receber
url = f'{BASE_URL}/update-webhook-received?instanceId={INSTANCE_ID}'
data = {"value": "https://webhook.site/b843e182-e69e-4a23-86ca-3efc2efc506d"}

response = requests.put(url, json=data, headers=HEADERS)
print(response.status_code, response.json())

# # Atualização no status de mensagens
# url = f'{BASE_URL}/update-webhook-message-status?instanceId={INSTANCE_ID}'
# data = {"value": "https://webhook.site/b843e182-e69e-4a23-86ca-3efc2efc506d"}
#
# response = requests.put(url, json=data, headers=HEADERS)
# print(response.status_code, response.json())
#
# # Atualização no status do chat
# url = f'{BASE_URL}/update-webhook-chat-presence?instanceId={INSTANCE_ID}'
# data = {"value": "https://webhook.site/bfc49dbf-c19a-438b-ab02-f4c698598280"}
#
# response = requests.put(url, json=data, headers=HEADERS)
# print(response.status_code, response.json())

import requests
import json

url = "https://api.w-api.app/v1/message/send-image"
instance_id = "SUA_INSTANCE_ID"
token = "SEU_TOKEN"

params = {"instanceId": instance_id}
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

payload = {
    "phone": "559199999999",
    "image": "https://via.placeholder.com/150",  # Exemplo de link de imagem
    "delayMessage": 15
}

response = requests.post(url, headers=headers, params=params, data=json.dumps(payload))

print(response.status_code)
print(response.json())

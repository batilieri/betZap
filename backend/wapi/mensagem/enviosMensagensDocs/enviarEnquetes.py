import requests

url = 'https://api.w-api.app/v1/message/send-poll?instanceId=SEU_INSTANCE_ID'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer SEU_TOKEN'
}

data = {
    "phone": "559199999999",
    "message": "NOME_DA_ENQUETE",
    "poll": ["Opção1", "Opção2", "Opção3"],
    "delayMessage": 15
}

response = requests.post(url, json=data, headers=headers)
print(response.json())

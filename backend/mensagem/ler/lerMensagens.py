import requests

url = 'https://api.w-api.app/v1/message/read-message?instanceId=SEU_INSTANCE_ID'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer SEU_TOKEN'
}

data = {
    "phone": "559199999999",
    "messageId": "ID_DA_MENSAGEM"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())

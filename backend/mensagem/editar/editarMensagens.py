import requests

url = 'https://api.w-api.app/v1/message/edit-message?instanceId=SEU_INSTANCE_ID'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer SEU_TOKEN'
}

data = {
    "phone": "559999999999",
    "text": "Mensagem editada!",
    "messageId": "GG2GLL7P6QHDCDIM6U3WK"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())

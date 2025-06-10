import requests

url = 'https://api.w-api.app/v1/message/send-contact?instanceId=SEU_INSTANCE_ID'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer SEU_TOKEN'
}
data = {
    "phone": "559199999999",
    "contactName": "WhizAPI Cloud Contato",
    "contactPhone": "559199999999",
    "delayMessage": 15
}

response = requests.post(url, json=data, headers=headers)
print(response.json())

import requests

url = 'https://api.w-api.app/v1/message/send-location?instanceId=SEU_INSTANCE_ID'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer SEU_TOKEN'
}
data = {
    "phone": "559199999999",
    "name": "Google Brasil",
    "address": "Av. Brg. Faria Lima, 3477 - Itaim Bibi, São Paulo - SP, 04538-133",
    "latitude": "-23.0696347",
    "longitude": "-50.4357913",
    "delayMessage": 15
}

response = requests.post(url, json=data, headers=headers)
print(response.json())

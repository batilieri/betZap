import requests

ID_INSTANCIA = "3B6XIW-ZTS923-GEAY6V"
ID_TOKEN = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"

url = f'https://api.w-api.app/v1/message/edit-message?instanceId={ID_INSTANCIA}'
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {ID_TOKEN}'
}

data = {
    "phone": "5569999267344",
    "text": "Minha Gostosaaaaa!!!!",
    "messageId": "545608C5A1070B4A10C0E72B9FB790A4"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())

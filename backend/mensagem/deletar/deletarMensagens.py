import requests

phone = "5569999267344"
messageId = "9D5BBC881CEA63335481453A3C056705"
instanceId = "3B6XIW-ZTS923-GEAY6V"

url = f'https://api.w-api.app/v1/message/delete-message?phone={phone}&messageId={messageId}&instanceId={instanceId}'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF'
}

response = requests.delete(url, headers=headers)
print(response.json())

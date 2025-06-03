import requests

url = "https://api.w-api.app/v1/webhook/update-webhook-delivery"
instance_id = "3B6XIW-ZTS923-GEAY6V"
token = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"

params = {
    "instanceId": instance_id
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

data = {
    "value": "https://webhook.site/0e6e92fd-c357-44e4-b1e5-067d6ae4cd0d"
}

response = requests.put(url, params=params, headers=headers, json=data)

print(response.status_code)
print(response.json())

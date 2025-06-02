import requests

phone = "559199999999"
messageId = "3EB0CDA59F4498C42E8426"
instanceId = "SEU_INSTANCE_ID"

url = f'https://api.w-api.app/v1/message/delete-message?phone={phone}&messageId={messageId}&instanceId={instanceId}'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer SEU_TOKEN'
}

response = requests.delete(url, headers=headers)
print(response.json())

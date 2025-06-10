import requests

url = 'https://api.w-api.app/v1/message/send-ptv?instanceId=SEU_INSTANCE_ID'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer SEU_TOKEN'
}
data = {
    "phone": "559199999999",
    "ptv": "https://link-do-video.mp4",
    "delayMessage": 15
}

response = requests.post(url, json=data, headers=headers)
print(response.json())

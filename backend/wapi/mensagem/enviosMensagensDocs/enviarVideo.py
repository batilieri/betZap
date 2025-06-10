import requests

url = 'https://api.w-api.app/v1/message/send-video?instanceId=SEU_INSTANCE_ID'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer SEU_TOKEN'
}
data = {
    "phone": "120363348570282291@g.us",
    "video": "https://link-do-video.mp4",
    "delayMessage": 15
}

response = requests.post(url, json=data, headers=headers)
print(response.json())

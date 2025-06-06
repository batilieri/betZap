url = "https://api.w-api.app/v1/message/send-gif"
params = {"instanceId": instance_id}

payload = {
    "phone": "559199999999",
    "gif": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",  # Exemplo de link mp4
    "delayMessage": 15
}

response = requests.post(url, headers=headers, params=params, data=json.dumps(payload))

print(response.status_code)
print(response.json())

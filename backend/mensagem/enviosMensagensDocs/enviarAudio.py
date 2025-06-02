url = "https://api.w-api.app/v1/message/send-audio"
params = {"instanceId": instance_id}

payload = {
    "phone": "120363348570282291@g.us",  # Exemplo de grupo
    "audio": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",  # Exemplo de link mp3
    "delayMessage": 15
}

response = requests.post(url, headers=headers, params=params, data=json.dumps(payload))

print(response.status_code)
print(response.json())

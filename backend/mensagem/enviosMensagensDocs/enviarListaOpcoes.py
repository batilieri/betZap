import requests

url = 'https://api.w-api.app/v1/message/send-list?instanceId=SEU_INSTANCE_ID'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer SEU_TOKEN'
}

data = {
    "phone": "559199999999",
    "title": "Título",
    "description": "Descrição",
    "buttonText": "Texto do Botão",
    "footerText": "Texto rodapé",
    "sections": [
        {
            "title": "Titulo 01",
            "rows": [
                {"title": "Titulo linha 01", "description": "Descrição linha 01,", "rowId": "rowId 001"},
                {"title": "Titulo linha 02", "description": "Descrição linha 02,", "rowId": "rowId 002"}
            ]
        },
        {
            "title": "Titulo 02",
            "rows": [
                {"title": "Titulo linha 01", "description": "Descrição linha 01,", "rowId": "rowId 001"},
                {"title": "Titulo linha 02", "description": "Descrição linha 02,", "rowId": "rowId 002"}
            ]
        }
    ]
}

response = requests.post(url, json=data, headers=headers)
print(response.json())

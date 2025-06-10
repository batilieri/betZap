import requests

# Configurações
url = "https://api.w-api.app/v1/chats/chat"
instance_id = "3B6XIW-ZTS923-GEAY6V"
phone_number = "556999267344@s.whatsapp.net"  # ou ID de grupo, ex: "120363149083623338@g.us"
token = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"

# Parâmetros da consulta
params = {
    "instanceId": instance_id,
    "phoneNumber": phone_number
}

# Cabeçalhos
headers = {
    "Authorization": f"Bearer {token}"
}

# Requisição GET
response = requests.get(url, headers=headers, params=params)

# Tratamento da resposta
if response.status_code == 200:
    dados = response.json()
    print("Metadata do Chat:")
    for chave, valor in dados.items():
        print(f"{chave}: {valor}")
else:
    print(f"Erro: {response.status_code}")
    print(response.text)


# Metadata do Chat:
# error: False
# message: Chat encontrado com sucesso.
# chat: {'id': '556999267344@s.whatsapp.net', 'name': 'AMOR 💘', 'lastMessageTime': 1748872244, 'profilePictureUrl':
#     'https://pps.whatsapp.net/v/t61.24694-24/462429652_2229319410767469_7773187573644695635_n.jpg?ccb=11-4&oh=01_Q5A'
#     'a1gGB4d0d_A8kNJL8KDV9D3pJzMzF2Tzh2nAKe17ZeyTKtw&oe=684ACD2F&_nc_sid=5e03e0&_nc_cat=100', 'about': None}

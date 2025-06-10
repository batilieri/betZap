import requests
from datetime import datetime

url = "https://api.w-api.app/v1/chats/fetch-chats"
instance_id = "3B6XIW-ZTS923-GEAY6V"
per_page = 20
page = 1
token = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"

params = {
    "instanceId": instance_id,
    "perPage": per_page,
    "page": page
}

headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    dados = response.json()

    print(f"Total de Chats: {dados.get('totalChats')}")
    print(f"Página Atual: {dados.get('currentPage')} de {dados.get('totalPages')}")
    print("\n=== Lista de Chats ===\n")

    for idx, chat in enumerate(dados.get('chats', []), start=1):
        chat_id = chat.get('id')
        name = chat.get('name') or 'Sem Nome'

        # Convertendo timestamp (epoch) para data legível
        last_msg_time = chat.get('lastMessageTime')
        if last_msg_time:
            last_msg_time = datetime.fromtimestamp(last_msg_time).strftime('%Y-%m-%d %H:%M:%S')
        else:
            last_msg_time = 'Sem Data'

        print(f"{idx}. Nome: {name}")
        print(f"   ID: {chat_id}")
        print(f"   Última Mensagem: {last_msg_time}\n")

else:
    print(f"Erro: {response.status_code}")
    print(response.text)



# exemplo de retorno:
# Total de Chats: 384
# Página Atual: 1 de 20
#
# === Lista de Chats ===
#
# 1. Nome: AMOR 💘
#    ID: 556999267344@s.whatsapp.net
#    Última Mensagem: 2025-06-02 09:50:44
#
# 2. Nome: Elizeu
#    ID: 556993291093-1609887215@g.us
#    Última Mensagem: 2025-05-26 17:58:34
#
# 3. Nome: Mami
#    ID: 556992962392@s.whatsapp.net
#    Última Mensagem: 2025-06-02 07:39:01

import json
import os

import requests
from mensagem import EnviaTexto
from mensagem import EnviaDocumento
from mensagem import EnviaImagem
from mensagem import EnviaGif
from mensagem import EnviaAudio
from mensagem import DeletaMensagem
from mensagem import EditarMensagem
from mensagem import EnviarReacao
from mensagem import RemoverReacao


class WhatsAppAPI:
    def __init__(self, instance_id, api_token, base_url="https://api.w-api.app/v1/"):
        """
        Inicializa a classe WhatsAppAPI para interagir com a API W-API do WhatsApp.

        Args:
            instance_id (str): ID da instância do WhatsApp.
            api_token (str): Token de autenticação da API.
            base_url (str): URL base da API.
        """
        self.instance_id = instance_id
        self.api_token = api_token
        self.base_url = base_url

    def checa_status_conexao(self, api_token, id_instance):
        """
        Verifica o status de conexão com a API.

        Args:
            api_token (str): Token de autenticação da API.
            id_instance (str): ID da instância do WhatsApp.

        Returns:
            str: Status da conexão ("connected" ou "disconnected").
        """
        url = f"{self.base_url}status?instanceId={id_instance}"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return "connected"
        else:
            return "disconnected"

    def envia_mensagem_texto(self, phone_number, message, delay_message=1):
        """
        Envia uma mensagem de texto para um contato via WhatsApp.

        Args:
            phone_number (str): Número de telefone do destinatário (com código do país, sem símbolos).
            message (str): Mensagem a ser enviada.
            delay_message (int, optional): Delay em segundos. Default: 1.

        Returns:
            dict: Resposta da API.
        """
        whatsapp_sender = EnviaTexto(self.instance_id, self.api_token, self.base_url)
        return whatsapp_sender.envia_mensagem_texto(phone_number, message, delay_message)

    def envia_documento(self, phone_number, file_path, caption="", delay=2):
        """
        Envia um documento para um contato via WhatsApp.

        Args:
            phone_number (str): Número de telefone do destinatário (com código do país, sem símbolos).
            file_path (str): Caminho completo do arquivo a ser enviado.
            caption (str, optional): Legenda opcional para o arquivo. Default: "".
            delay (int, optional): Delay em segundos. Default: 2.

        Returns:
            dict: Resultado do envio.
        """
        whatsapp_docs = EnviaDocumento(self.base_url, self.instance_id, self.api_token)
        return whatsapp_docs.enviar_arquivo_local(phone_number, file_path, caption, delay)

    def enviar_imagem(self, phone_number, image_path, caption="", delay_message=1):
        """
        Envia uma imagem para um contato via WhatsApp.

        Args:
            phone_number (str): Número de telefone do destinatário (com código do país, sem símbolos).
            image_path (str): Caminho completo da imagem a ser enviada.
            caption (str, optional): Legenda opcional para a imagem. Default: "".
            delay_message (int, optional): Delay em segundos. Default: 1.

        Returns:
            dict: Resultado do envio.
        """
        whatsapp_image = EnviaImagem(self.instance_id, self.api_token)
        return whatsapp_image.enviar(phone_number, image_path, caption, delay_message)

    def enviarGif(self, phone_number, gif_source, caption="", delay_message=1):
        """
        Envia um GIF ou vídeo MP4 para um contato via WhatsApp.

        Args:
            phone_number (str): Número de telefone do destinatário (com código do país, sem símbolos).
            gif_source (str): URL do GIF/MP4 ou caminho local do arquivo.
            caption (str, optional): Legenda opcional para o GIF. Default: "".
            delay_message (int, optional): Delay em segundos. Default: 1.

        Returns:
            dict: Resultado do envio.
        """
        whatsapp_gif = EnviaGif(self.instance_id, self.api_token)
        return whatsapp_gif.enviar(phone_number, gif_source, caption, delay_message)

    def enviar_audio(self, phone_number, audio_source, delay_message=1):
        """
        Envia um áudio para um contato via WhatsApp.

        Args:
            phone_number (str): Número de telefone do destinatário (com código do país, sem símbolos).
            audio_source (str): URL do áudio ou caminho local do arquivo.
            delay_message (int, optional): Delay em segundos. Default: 1.

        Returns:
            dict: Resultado do envio.
        """
        whatsapp_audio = EnviaAudio(self.instance_id, self.api_token)
        return whatsapp_audio.enviar(phone_number, audio_source)

    def deleta_mensagem(self, phone_number, message_ids):
        """
        Deleta uma ou várias mensagens enviadas.

        Args:
            phone_number (str): Número de telefone do destinatário (com código do país, sem símbolos).
            message_ids (str ou list): ID(s) da(s) mensagem(ns) a serem deletadas.
                - String: deleta uma mensagem
                - Lista: deleta várias mensagens

        Returns:
            dict: Resultado da operação.
        """
        deleter = DeletaMensagem(self.instance_id, self.api_token)
        return deleter.deletar(phone_number, message_ids)

    def editar_mensagem(self, phone, message_id, new_text):
        """
        Edita uma mensagem já enviada.

        Args:
            phone (str): Número do telefone (formato: 5569999267344).
            message_id (str): ID da mensagem a ser editada.
            new_text (str): Novo texto da mensagem.

        Returns:
            dict: Resposta da API.
        """
        editor = EditarMensagem(self.instance_id, self.api_token)
        return editor.editar_mensagem(phone, message_id, new_text)

    def enviar_reacao(self, phone, message_id, reaction="👍", delay=2):

        reacao = EnviarReacao(self.instance_id, self.api_token)
        return reacao.enviar_reacao(
            phone=phone,
            message_id=message_id,
            reaction=reaction,
            delay=delay
        )

    def removerReacao(self, phone, menssagem_id, dalay):

        removeRecao = RemoverReacao(self.instance_id, self.api_token)
        return removeRecao.remover_reacao(
            phone=phone,
            message_id=menssagem_id,
            delay_message=dalay
        )


if __name__ == "__main__":
    # Configurações da API - substitua pelos seus dados reais
    INSTANCE_ID = "3B6XIW-ZTS923-GEAY6V"
    API_TOKEN = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"
    PHONE_NUMBER = "5569993291093"
    MESSAGE = "teste"

    whatsapp_api = WhatsAppAPI(INSTANCE_ID, API_TOKEN)
    # Envia a mensagem
    result = whatsapp_api.envia_mensagem_texto(PHONE_NUMBER, MESSAGE, delay_message=1)
    print("Resultado do envio:", result)

    #
    # envia Documentos
    # resultado = whatsapp_api.envia_documento(PHONE_NUMBER,
    #                            r"C:\Users\eliba\PycharmProjects\betZap\backend\wapi\imagens\d327976b-1152-43e2-8ae9"
    #                            r"-fee503914ee9_image.jpeg",
    #                                          caption="Segue em anexo o relatório solicitado.",
    #                                          delay=5)
    #
    # print("Resultado do envio do documento:", resultado)

    # Envia Imagem
    # resposta = whatsapp_api.enviar_imagem(
    #     phone_number=PHONE_NUMBER,
    #     image_path=r"C:\Users\eliba\PycharmProjects\betZap\backend\wapi\imagens\d327976b-1152-43e2-8ae9-fee503914ee9_image.jpeg",
    #     caption="Minha imagem"
    # )
    # print(resposta)

    # Envia GIF
    # resposta_gif = whatsapp_api.enviarGif(
    #     phone_number=PHONE_NUMBER,
    #     gif_source=r"C:\Users\eliba\PycharmProjects\betZap\backend\gif\9wle8b.mp4",
    #     caption="Meu GIF",
    #     delay_message=5
    # )
    # print(resposta_gif)
    # Envia Áudio
    # resposta_audio = whatsapp_api.enviar_audio(
    #     phone_number=PHONE_NUMBER,
    #     audio_source=r"C:\Users\eliba\PycharmProjects\betZap\backend\wapi\midias\audios\ColdPlay - The Scientist.mp3",
    #     delay_message=5
    # )
    # print(resposta_audio)

    # Deleta Mensagem
    # resposta_deletar = whatsapp_api.deleta_mensagem(
    #     phone_number=PHONE_NUMBER,
    #     message_ids=["D46F85EE75A8777482C72FC621620844","D0E9639179B8E2C178C599D59206552E"]
    # )
    # print("Resultado da deleção:", resposta_deletar)

    # Edita Mensagem
    # resposta_editar = whatsapp_api.editar_mensagem(
    #     phone=PHONE_NUMBER,
    #     message_id="B0E6823BE7F78D8BEB9E32EC3A2EF31A",
    #     new_text="Mensagem editada"
    # )
    # Enviar Reacao
    # reacao = whatsapp_api.enviar_reacao(
    #     PHONE_NUMBER,
    #     message_id="901F3A47977FBA510639A4FAF83846A3",
    #     reaction="❤"
    #
    # )
    #Remove reacao

    # reacao = whatsapp_api.removerReacao(
    #     PHONE_NUMBER,
    #     menssagem_id="Q05CTOLUB30BTJ2HHAYGT", # ID DO DA REAÇÃO
    #     dalay=1)
    # print(reacao)

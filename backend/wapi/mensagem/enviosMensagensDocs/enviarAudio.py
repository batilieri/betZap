import requests
import json
import base64
import os
import mimetypes
import tempfile

# Para gravação de áudio (instale com: pip install pyaudio)
try:
    import pyaudio
    import wave

    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("⚠️  PyAudio não encontrado. Para gravar áudio instale: pip install pyaudio")


class EnviaAudio:
    """Classe para enviar áudios via WhatsApp - arquivos, URLs ou gravação do microfone."""

    def __init__(self, instance_id, api_token, base_url="https://api.w-api.app/v1/message"):
        self.instance_id = instance_id
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_token}"
        }

    def enviar(self, phone_number, fonte_audio, **kwargs):
        """
        Método único para enviar áudios.
        Detecta automaticamente: arquivo local, URL, ou grava do microfone.

        Args:
            phone_number (str): Número/grupo para enviar
            fonte_audio (str): 
                - Caminho do arquivo: "/pasta/audio.mp3"
                - URL: "https://site.com/audio.mp3" 
                - "microfone" ou "gravar": grava do microfone
            **kwargs: delay_message, duracao_gravacao, etc.

        Returns:
            dict: Resultado com success/error
        """
        try:
            delay_message = kwargs.get('delay_message', 1)

            # Validação básica do número/grupo
            if not phone_number or len(phone_number) < 5:
                return {"success": False, "error": "Número/grupo inválido"}

            # Detecta o tipo de fonte
            tipo_fonte = self._detectar_tipo_audio(fonte_audio)

            if tipo_fonte == "microfone":
                return self._enviar_do_microfone(phone_number, delay_message, **kwargs)

            elif tipo_fonte == "url":
                return self._enviar_url_audio(phone_number, fonte_audio, delay_message)

            elif tipo_fonte == "arquivo":
                return self._enviar_arquivo_audio(phone_number, fonte_audio, delay_message)

            else:
                return {"success": False, "error": "Fonte de áudio não identificada"}

        except Exception as e:
            return {"success": False, "error": f"Erro: {str(e)}"}

    def _detectar_tipo_audio(self, fonte):
        """Detecta o tipo da fonte de áudio."""
        fonte_lower = fonte.lower().strip()

        # Microfone
        if fonte_lower in ["microfone", "gravar", "mic", "microphone", "record"]:
            return "microfone"

        # URLs
        if fonte.startswith(('http://', 'https://')):
            return "url"

        # Arquivos locais
        if (':\\' in fonte or
                fonte.startswith('/') or
                fonte.startswith('./') or
                fonte.startswith('../') or
                os.path.exists(fonte)):
            return "arquivo"

        # URLs sem protocolo
        if '.' in fonte and '/' in fonte:
            return "url"

        return "desconhecido"

    def _enviar_do_microfone(self, phone_number, delay_message, **kwargs):
        """Grava áudio do microfone e envia."""
        if not PYAUDIO_AVAILABLE:
            return {
                "success": False,
                "error": "PyAudio não instalado. Execute: pip install pyaudio"
            }

        try:
            duracao = kwargs.get('duracao_gravacao', 5)  # 5 segundos padrão

            print(f"🎤 Gravando áudio por {duracao} segundos...")
            arquivo_temp = self._gravar_audio(duracao)

            if not arquivo_temp:
                return {"success": False, "error": "Erro na gravação"}

            print("✅ Gravação concluída! Enviando...")

            # Envia o arquivo gravado
            resultado = self._enviar_arquivo_audio(phone_number, arquivo_temp, delay_message)

            # Remove arquivo temporário
            try:
                os.remove(arquivo_temp)
            except:
                pass

            return resultado

        except Exception as e:
            return {"success": False, "error": f"Erro na gravação: {str(e)}"}

    def _gravar_audio(self, duracao_segundos):
        """Grava áudio do microfone."""
        try:
            # Configurações de áudio
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100

            # Inicializa PyAudio
            p = pyaudio.PyAudio()

            # Abre stream de gravação
            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

            frames = []

            # Grava por X segundos
            for i in range(0, int(RATE / CHUNK * duracao_segundos)):
                data = stream.read(CHUNK)
                frames.append(data)

            # Para gravação
            stream.stop_stream()
            stream.close()
            p.terminate()

            # Salva em arquivo temporário
            arquivo_temp = tempfile.mktemp(suffix=".wav")

            with wave.open(arquivo_temp, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))

            return arquivo_temp

        except Exception as e:
            print(f"Erro na gravação: {e}")
            return None

    def _enviar_url_audio(self, phone_number, audio_url, delay_message):
        """Envia áudio via URL."""
        try:
            payload = {
                "phone": phone_number,
                "audio": audio_url,
                "delayMessage": delay_message
            }

            return self._fazer_requisicao(payload)

        except Exception as e:
            return {"success": False, "error": f"Erro ao enviar URL: {str(e)}"}

    def _enviar_arquivo_audio(self, phone_number, caminho_audio, delay_message):
        """Envia arquivo de áudio local."""
        try:
            # Verifica se existe
            if not os.path.exists(caminho_audio):
                return {"success": False, "error": f"Arquivo não encontrado: {caminho_audio}"}

            # Valida extensão
            if not self._audio_valido(caminho_audio):
                return {"success": False, "error": "Formato não suportado. Use: mp3, wav, ogg, m4a"}

            # Converte para base64
            audio_base64 = self._audio_to_base64(caminho_audio)
            if not audio_base64:
                return {"success": False, "error": "Erro na conversão para base64"}

            payload = {
                "phone": phone_number,
                "audio": audio_base64,
                "delayMessage": delay_message
            }

            return self._fazer_requisicao(payload)

        except Exception as e:
            return {"success": False, "error": f"Erro ao processar arquivo: {str(e)}"}

    def _audio_valido(self, arquivo):
        """Verifica se é um arquivo de áudio válido."""
        extensoes = {'.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac'}
        ext = os.path.splitext(arquivo.lower())[1]
        return ext in extensoes

    def _audio_to_base64(self, arquivo):
        """Converte arquivo de áudio para base64."""
        try:
            # Detecta MIME type
            mime_type, _ = mimetypes.guess_type(arquivo)
            if not mime_type or not mime_type.startswith('audio/'):
                ext = os.path.splitext(arquivo.lower())[1]
                mime_types = {
                    '.mp3': 'audio/mpeg',
                    '.wav': 'audio/wav',
                    '.ogg': 'audio/ogg',
                    '.m4a': 'audio/mp4',
                    '.aac': 'audio/aac',
                    '.flac': 'audio/flac'
                }
                mime_type = mime_types.get(ext, 'audio/mpeg')

            # Lê e converte
            with open(arquivo, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')

            return f"data:{mime_type};base64,{encoded}"

        except Exception as e:
            print(f"Erro na conversão: {e}")
            return None

    def _fazer_requisicao(self, payload):
        """Faz requisição para API."""
        try:
            url = f"{self.base_url}/send-audio"
            params = {"instanceId": self.instance_id}

            response = requests.post(
                url,
                headers=self.headers,
                params=params,
                data=json.dumps(payload),
                timeout=60  # Timeout maior para áudios
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "message": "Áudio enviado com sucesso!"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "details": response.text[:200]
                }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout - áudio muito grande?"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Sem conexão"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def gravar_e_salvar(self, caminho_destino, duracao_segundos=5):
        """
        Método extra: apenas grava áudio e salva em arquivo.
        Útil para gravar e depois enviar separadamente.
        """
        if not PYAUDIO_AVAILABLE:
            return {"success": False, "error": "PyAudio não instalado"}

        try:
            print(f"🎤 Gravando por {duracao_segundos} segundos...")
            arquivo_temp = self._gravar_audio(duracao_segundos)

            if arquivo_temp:
                # Move para destino final
                import shutil
                shutil.move(arquivo_temp, caminho_destino)
                print(f"✅ Áudio salvo em: {caminho_destino}")
                return {"success": True, "arquivo": caminho_destino}
            else:
                return {"success": False, "error": "Erro na gravação"}

        except Exception as e:
            return {"success": False, "error": str(e)}


# Exemplo de uso completo
# if __name__ == "__main__":
#     audio = EnviaAudio("3B6XIW-ZTS923-GEAY6V", "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF")
#
#     # 1. Enviar arquivo local
#     result1 = audio.enviar("69993291093",
#                            r"C:\Users\eliba\PycharmProjects\betZap\backend\wapi\midias\audios\ColdPlay - The Scientist.mp3")

    # 2. Enviar URL
    #result2 = audio.enviar("120363348570282291@g.us",
    #                       "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    #                       delay_message=15)

    # 3. Gravar do microfone e enviar (5 segundos)
    #result3 = audio.enviar("120363348570282291@g.us", "microfone", duracao_gravacao=5)

    # 4. Gravar do microfone (10 segundos)
    #result4 = audio.enviar("120363348570282291@g.us", "gravar", duracao_gravacao=10)

    # 5. Apenas gravar e salvar arquivo
    #result5 = audio.gravar_e_salvar("meu_audio.wav", duracao_segundos=8)
    # print(result1)

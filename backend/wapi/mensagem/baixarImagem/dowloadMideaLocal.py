import requests
from pathlib import Path
from urllib.parse import urlparse


def download_file_from_url(url: str, output_path: str = None, headers: dict = None) -> bool:
    """Baixa arquivo de uma URL direta"""
    try:
        response = requests.get(url, headers=headers or {}, stream=True, timeout=30)
        response.raise_for_status()

        # Se não especificar caminho, extrai nome do URL
        if not output_path:
            parsed_url = urlparse(url)
            filename = Path(parsed_url.path).name or "downloaded_file"
            output_path = filename

        # Garante que diretório existe
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ Arquivo baixado: {output_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao baixar: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


# Adicionar método à classe WhatsAppMediaDecryptor
def download_direct_media(self, file_url: str, output_dir: str = "direct_downloads") -> bool:
    """Baixa mídia diretamente de URL da API"""
    try:
        # Extrai nome do arquivo da URL
        parsed_url = urlparse(file_url)
        filename = Path(parsed_url.path).name

        if not filename:
            filename = "media_file"

        output_path = Path(output_dir) / filename

        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        return download_file_from_url(file_url, str(output_path), headers)

    except Exception as e:
        print(f"❌ Erro ao processar URL: {e}")
        return False


# Exemplo de uso
def main():
    # URL do seu exemplo
    diretorio = r"C:\Users\Administrador\PycharmProjects\betZap\backend\wapi\mensagem\baixarImagem\downloads_whatsapp\audios\audiosBaixados"
    file_url = "https://api.w-api.app/media/file/b3bfe10e-28c3-4225-b907-67171f807139_audio.oga"

    # Baixar diretamente
    success = download_file_from_url(file_url, f"{diretorio}/teste.oga")

    if success:
        print("Arquivo baixado com sucesso!")
    else:
        print("Falha no download")

main()
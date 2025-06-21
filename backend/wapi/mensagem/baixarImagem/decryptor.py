import requests
import json
import os
import base64
from typing import Dict, List, Optional
from pathlib import Path


class WhatsAppMediaDecryptor:
    def __init__(self, instance_id: str, bearer_token: str):
        self.instance_id = instance_id
        self.bearer_token = bearer_token
        self.base_url = "https://api.w-api.app/v1/message/download-media"

    def load_metadata_from_json(self, json_path: str) -> List[Dict]:
        """Carrega metadados do arquivo JSON fornecido"""
        try:
            # Converte para Path absoluto para melhor resolução
            json_file = Path(json_path)
            if not json_file.exists():
                print(f"Arquivo não encontrado: {json_file.absolute()}")
                return []

            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('arquivos', [])
        except FileNotFoundError:
            print(f"Arquivo não encontrado: {json_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}")
            return []
        except Exception as e:
            print(f"Erro ao carregar JSON: {e}")
            return []

    def download_media(self, media_key: str, direct_path: str,
                       media_type: str, mimetype: str) -> Optional[bytes]:
        """Baixa mídia descriptografada da API"""

        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }

        params = {
            'instanceId': self.instance_id
        }

        payload = {
            'mediaKey': media_key,
            'directPath': direct_path,
            'type': media_type,
            'mimetype': mimetype
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                params=params,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return response.content
            else:
                print(f"Erro na API: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição: {e}")
            return None

    def process_media_file(self, arquivo: Dict, output_base_dir: str = "decrypted_media") -> bool:
        """Processa um arquivo de mídia individual"""

        # Extrai informações do arquivo
        media_type = arquivo.get('type')
        sender_name = arquivo.get('sender_name', 'Unknown')
        file_name = arquivo.get('file_name')
        original_data = arquivo.get('original_data', {})

        # Informações necessárias para descriptografia
        media_key = original_data.get('mediaKey')
        direct_path = original_data.get('directPath')
        mimetype = arquivo.get('mimetype')

        if not media_key or not direct_path:
            print(f"❌ Metadados incompletos para {file_name}")
            return False

        # Cria diretório específico para o tipo de mídia
        type_dir_map = {
            'audio': 'audios',
            'image': 'imagens',
            'video': 'videos',
            'sticker': 'stickers',
            'document': 'documentos'
        }

        type_dir = type_dir_map.get(media_type, 'outros')
        output_dir = os.path.join(output_base_dir, type_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        print(f"📥 Baixando {media_type}: {file_name} ({sender_name})")

        # Baixa o arquivo descriptografado
        media_data = self.download_media(media_key, direct_path, media_type, mimetype)

        if media_data:
            output_path = os.path.join(output_dir, file_name)

            try:
                with open(output_path, 'wb') as f:
                    f.write(media_data)
                print(f"✅ Salvo: {output_path}")
                return True
            except Exception as e:
                print(f"❌ Erro ao salvar {file_name}: {e}")
                return False
        else:
            print(f"❌ Falha ao baixar {file_name}")
            return False

    def decrypt_all_media(self, json_path: str, output_dir: str = "decrypted_media") -> Dict[str, int]:
        """Descriptografa todos os arquivos de mídia do JSON"""

        print("Carregando metadados do arquivo JSON...")
        arquivos = self.load_metadata_from_json(json_path)

        if not arquivos:
            print("Nenhum arquivo encontrado no JSON")
            return {"success": 0, "failed": 0}

        # Estatísticas por tipo
        tipos = {}
        for arquivo in arquivos:
            tipo = arquivo.get('type', 'unknown')
            tipos[tipo] = tipos.get(tipo, 0) + 1

        print(f"📊 Encontrados {len(arquivos)} arquivos:")
        for tipo, count in tipos.items():
            print(f"   {tipo}: {count}")

        success_count = 0
        failed_count = 0

        for i, arquivo in enumerate(arquivos, 1):
            print(f"\n[{i}/{len(arquivos)}]", end=" ")
            if self.process_media_file(arquivo, output_dir):
                success_count += 1
            else:
                failed_count += 1

        print(f"\n📊 Resultado Final:")
        print(f"✅ Sucessos: {success_count}")
        print(f"❌ Falhas: {failed_count}")

        return {"success": success_count, "failed": failed_count}

    def decrypt_by_type(self, json_path: str, media_types: List[str] = None,
                        output_dir: str = "decrypted_media") -> Dict[str, int]:
        """Descriptografa apenas tipos específicos de mídia"""

        if media_types is None:
            media_types = ['audio']  # Padrão apenas áudios

        print(f"Filtrando apenas: {', '.join(media_types)}")

        arquivos = self.load_metadata_from_json(json_path)
        arquivos_filtrados = [a for a in arquivos if a.get('type') in media_types]

        print(f"📊 {len(arquivos_filtrados)} arquivos do(s) tipo(s) selecionado(s)")

        success_count = 0
        failed_count = 0

        for i, arquivo in enumerate(arquivos_filtrados, 1):
            print(f"\n[{i}/{len(arquivos_filtrados)}]", end=" ")
            if self.process_media_file(arquivo, output_dir):
                success_count += 1
            else:
                failed_count += 1

        return {"success": success_count, "failed": failed_count}


def main():
    # Configuração (substitua pelos seus valores)
    INSTANCE_ID = "3B6XIW-ZTS923-GEAY6V"
    BEARER_TOKEN = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"

    # Usar caminho absoluto ou relativo ao diretório atual
    base_dir = Path(__file__).parent
    JSON_FILE_PATH = base_dir / "downloads_whatsapp" / "indice_midias.json"
    OUTPUT_DIR = base_dir / "downloads_whatsapp" / "audios" / "descriptografados"

    # Converte para string para compatibilidade
    JSON_FILE_PATH = str(JSON_FILE_PATH)
    OUTPUT_DIR = str(OUTPUT_DIR)

    # Verifica se o arquivo JSON existe antes de prosseguir
    if not Path(JSON_FILE_PATH).exists():
        print(f"❌ Arquivo JSON não encontrado: {JSON_FILE_PATH}")
        print(f"📁 Diretório atual: {Path.cwd()}")
        return

    # Inicializa o descriptografador
    decryptor = WhatsAppMediaDecryptor(INSTANCE_ID, BEARER_TOKEN)

    print("🚀 WhatsApp Media Decryptor")
    print("=" * 50)

    # Opções de processamento
    choice = input("""
Escolha uma opção:
1 - Descriptografar TODOS os arquivos (imagens, vídeos, áudios, stickers)
2 - Descriptografar apenas ÁUDIOS
3 - Descriptografar apenas IMAGENS
4 - Descriptografar ÁUDIOS + VÍDEOS
5 - Escolher tipos específicos

Digite sua opção (1-5): """)

    if choice == "1":
        # Todos os arquivos
        result = decryptor.decrypt_all_media(JSON_FILE_PATH, OUTPUT_DIR)

    elif choice == "2":
        # Apenas áudios
        result = decryptor.decrypt_by_type(JSON_FILE_PATH, ['audio'], OUTPUT_DIR)

    elif choice == "3":
        # Apenas imagens
        result = decryptor.decrypt_by_type(JSON_FILE_PATH, ['image'], OUTPUT_DIR)

    elif choice == "4":
        # Áudios e vídeos
        result = decryptor.decrypt_by_type(JSON_FILE_PATH, ['audio', 'video'], OUTPUT_DIR)

    elif choice == "5":
        # Tipos específicos
        print("\nTipos disponíveis: image, video, audio, sticker, document")
        tipos_input = input("Digite os tipos separados por vírgula: ")
        tipos = [t.strip() for t in tipos_input.split(',')]
        result = decryptor.decrypt_by_type(JSON_FILE_PATH, tipos, OUTPUT_DIR)

    else:
        print("Opção inválida!")
        return

    # Resultado final
    if result["success"] > 0:
        print(f"\n🎉 {result['success']} arquivos descriptografados com sucesso!")
        print(f"📁 Arquivos salvos em: {OUTPUT_DIR}")
        print(f"\n📁 Estrutura criada:")
        print(f"   {OUTPUT_DIR}/")
        print(f"   ├── audios/")
        print(f"   ├── imagens/")
        print(f"   ├── videos/")
        print(f"   ├── stickers/")
        print(f"   └── documentos/")
    else:
        print("❌ Nenhum arquivo foi descriptografado com sucesso.")


if __name__ == "__main__":
    main()
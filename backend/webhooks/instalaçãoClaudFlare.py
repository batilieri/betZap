#!/usr/bin/env python3
"""
Instalador Automático do Cloudflared
Detecta sistema e instala automaticamente sem intervenção do usuário
"""

import subprocess
import platform
import time

import requests
import os
import shutil
import sys
import zipfile
import tarfile
from pathlib import Path


class CloudflaredAutoInstaller:
    """Instalador automático do cloudflared para todos os sistemas"""

    def __init__(self):
        self.sistema = platform.system().lower()
        self.arquitetura = platform.machine().lower()
        self.cloudflared_path = None
        self.temp_dir = Path("./temp_cloudflared")

    def detectar_sistema(self):
        """Detecta sistema operacional e arquitetura"""
        print(f"🔍 Sistema detectado: {self.sistema}")
        print(f"🏗️  Arquitetura: {self.arquitetura}")

        # Mapear arquiteturas
        arch_map = {
            'x86_64': 'amd64',
            'amd64': 'amd64',
            'arm64': 'arm64',
            'aarch64': 'arm64',
            'i386': '386',
            'i686': '386'
        }

        self.arch_normalized = arch_map.get(self.arquitetura, 'amd64')
        print(f"📦 Arquitetura normalizada: {self.arch_normalized}")

    def verificar_cloudflared_existente(self):
        """Verifica se cloudflared já está instalado"""
        print("\n🔍 Verificando cloudflared existente...")

        # Locais possíveis do cloudflared
        possíveis_caminhos = [
            'cloudflared',
            'cloudflared.exe',
            './cloudflared',
            './cloudflared.exe',
            '/usr/local/bin/cloudflared',
            '/usr/bin/cloudflared',
            str(Path.home() / 'bin' / 'cloudflared'),
        ]

        for caminho in possíveis_caminhos:
            try:
                result = subprocess.run([caminho, '--version'],
                                        capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ Cloudflared encontrado: {caminho}")
                    print(f"📋 Versão: {result.stdout.strip()}")
                    self.cloudflared_path = caminho
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        print("❌ Cloudflared não encontrado")
        return False

    def obter_url_download(self):
        """Obtém URL de download baseada no sistema"""
        base_url = "https://github.com/cloudflare/cloudflared/releases/latest/download"

        urls = {
            'windows': {
                'amd64': f"{base_url}/cloudflared-windows-amd64.exe",
                '386': f"{base_url}/cloudflared-windows-386.exe"
            },
            'linux': {
                'amd64': f"{base_url}/cloudflared-linux-amd64",
                'arm64': f"{base_url}/cloudflared-linux-arm64",
                '386': f"{base_url}/cloudflared-linux-386"
            },
            'darwin': {  # macOS
                'amd64': f"{base_url}/cloudflared-darwin-amd64.tgz",
                'arm64': f"{base_url}/cloudflared-darwin-arm64.tgz"
            }
        }

        sistema_urls = urls.get(self.sistema)
        if not sistema_urls:
            raise ValueError(f"Sistema {self.sistema} não suportado")

        url = sistema_urls.get(self.arch_normalized)
        if not url:
            # Fallback para amd64
            url = sistema_urls.get('amd64')

        if not url:
            raise ValueError(f"Arquitetura {self.arch_normalized} não suportada para {self.sistema}")

        return url

    def criar_diretorio_temp(self):
        """Cria diretório temporário"""
        self.temp_dir.mkdir(exist_ok=True)
        print(f"📁 Diretório temporário: {self.temp_dir}")

    def baixar_cloudflared(self, url):
        """Baixa cloudflared do GitHub"""
        print(f"\n⬇️  Baixando cloudflared...")
        print(f"🔗 URL: {url}")

        filename = url.split('/')[-1]
        filepath = self.temp_dir / filename

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(filepath, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r📊 Progresso: {percent:.1f}% ({downloaded:,}/{total_size:,} bytes)",
                                  end="", flush=True)

            print(f"\n✅ Download concluído: {filepath}")
            return filepath

        except Exception as e:
            print(f"\n❌ Erro no download: {e}")
            raise

    def extrair_arquivo(self, filepath):
        """Extrai arquivo se necessário (macOS)"""
        if filepath.suffix == '.tgz':
            print(f"📦 Extraindo arquivo comprimido...")

            with tarfile.open(filepath, 'r:gz') as tar:
                tar.extractall(self.temp_dir)

            # Procurar executável extraído
            for file in self.temp_dir.iterdir():
                if file.name.startswith('cloudflared') and file.is_file():
                    return file

        return filepath

    def instalar_cloudflared(self, filepath):
        """Instala cloudflared no local apropriado"""
        print(f"\n🔧 Instalando cloudflared...")

        if self.sistema == 'windows':
            return self._instalar_windows(filepath)
        else:
            return self._instalar_unix(filepath)

    def _instalar_windows(self, filepath):
        """Instalação no Windows"""
        # Tentar instalar em ordem de preferência
        destinos = [
            Path('./cloudflared.exe'),  # Pasta atual
            Path.home() / 'bin' / 'cloudflared.exe',  # Pasta pessoal
        ]

        for destino in destinos:
            try:
                # Criar diretório se necessário
                destino.parent.mkdir(parents=True, exist_ok=True)

                # Copiar arquivo
                shutil.copy2(filepath, destino)

                # Testar se funciona
                result = subprocess.run([str(destino), '--version'],
                                        capture_output=True, text=True, timeout=5)

                if result.returncode == 0:
                    print(f"✅ Cloudflared instalado: {destino}")
                    self.cloudflared_path = str(destino)

                    # Adicionar ao PATH se necessário
                    if destino.parent not in [Path(p) for p in os.environ.get('PATH', '').split(os.pathsep)]:
                        print(f"💡 Adicione ao PATH: {destino.parent}")

                    return True

            except Exception as e:
                print(f"⚠️  Falha em {destino}: {e}")
                continue

        return False

    def _instalar_unix(self, filepath):
        """Instalação no Linux/macOS"""
        # Tentar instalar em ordem de preferência
        destinos = [
            '/usr/local/bin/cloudflared',  # Sistema (requer sudo)
            str(Path.home() / 'bin' / 'cloudflared'),  # Usuário
            './cloudflared',  # Pasta atual
        ]

        for destino in destinos:
            try:
                destino_path = Path(destino)

                # Criar diretório se necessário
                destino_path.parent.mkdir(parents=True, exist_ok=True)

                # Copiar arquivo
                if destino.startswith('/usr/'):
                    # Tentar com sudo
                    result = subprocess.run(['sudo', 'cp', str(filepath), destino],
                                            capture_output=True)
                    if result.returncode == 0:
                        subprocess.run(['sudo', 'chmod', '+x', destino])
                    else:
                        continue
                else:
                    shutil.copy2(filepath, destino)
                    os.chmod(destino, 0o755)

                # Testar se funciona
                result = subprocess.run([destino, '--version'],
                                        capture_output=True, text=True, timeout=5)

                if result.returncode == 0:
                    print(f"✅ Cloudflared instalado: {destino}")
                    self.cloudflared_path = destino
                    return True

            except Exception as e:
                print(f"⚠️  Falha em {destino}: {e}")
                continue

        return False

    def limpar_temporarios(self):
        """Remove arquivos temporários"""
        try:
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Arquivos temporários removidos")
        except Exception as e:
            print(f"⚠️  Erro ao limpar temporários: {e}")

    def instalar_automatico(self):
        """Executa instalação automática completa"""
        print("🚀 INSTALADOR AUTOMÁTICO DO CLOUDFLARED")
        print("=" * 50)

        try:
            # 1. Detectar sistema
            self.detectar_sistema()

            # 2. Verificar se já existe
            if self.verificar_cloudflared_existente():
                return True

            print("\n📦 Iniciando instalação automática...")

            # 3. Obter URL de download
            url = self.obter_url_download()

            # 4. Criar diretório temporário
            self.criar_diretorio_temp()

            # 5. Baixar
            filepath = self.baixar_cloudflared(url)

            # 6. Extrair se necessário
            filepath = self.extrair_arquivo(filepath)

            # 7. Instalar
            sucesso = self.instalar_cloudflared(filepath)

            # 8. Limpar
            self.limpar_temporarios()

            if sucesso:
                print(f"\n🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
                print(f"📍 Localização: {self.cloudflared_path}")

                # Verificação final
                if self.verificar_cloudflared_existente():
                    print("✅ Verificação final: OK")
                    return True
                else:
                    print("❌ Verificação final: Falhou")
                    return False
            else:
                print(f"\n❌ FALHA NA INSTALAÇÃO")
                return False

        except Exception as e:
            print(f"\n❌ ERRO CRÍTICO: {e}")
            self.limpar_temporarios()
            return False

    def obter_caminho_cloudflared(self):
        """Retorna o caminho do cloudflared instalado"""
        return self.cloudflared_path


def instalar_cloudflared_automatico():
    """Função helper para usar em outros scripts"""
    installer = CloudflaredAutoInstaller()

    if installer.instalar_automatico():
        return installer.obter_caminho_cloudflared()
    else:
        return None


# Integração com o webhook manager
class WebhookManagerComAutoInstall:
    """Webhook manager que instala cloudflared automaticamente"""

    def __init__(self, port=5000):
        self.port = port
        self.tunnel_url = None
        self.tunnel_process = None
        self.cloudflared_path = None

    def garantir_cloudflared(self):
        """Garante que cloudflared está instalado"""
        print("🔍 Verificando cloudflared...")

        installer = CloudflaredAutoInstaller()

        # Verificar se já existe
        if installer.verificar_cloudflared_existente():
            self.cloudflared_path = installer.obter_caminho_cloudflared()
            return True

        # Instalar automaticamente
        print("📦 Cloudflared não encontrado. Instalando automaticamente...")

        if installer.instalar_automatico():
            self.cloudflared_path = installer.obter_caminho_cloudflared()
            return True
        else:
            print("❌ Falha na instalação automática")
            return False

    def criar_tunnel(self):
        """Cria túnel (garante instalação primeiro)"""
        if not self.garantir_cloudflared():
            return False

        print(f"\n🚀 Criando túnel na porta {self.port}...")

        try:
            comando = [
                self.cloudflared_path,
                'tunnel', '--url', f'http://localhost:{self.port}'
            ]

            self.tunnel_process = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Aguardar URL
            timeout = 30
            start_time = time.time()

            while (time.time() - start_time) < timeout:
                line = self.tunnel_process.stdout.readline()

                if line and 'trycloudflare.com' in line:
                    words = line.split()
                    for word in words:
                        if 'https://' in word and 'trycloudflare.com' in word:
                            self.tunnel_url = word.strip()
                            print(f"✅ Túnel criado: {self.tunnel_url}")
                            return True

                if self.tunnel_process.poll() is not None:
                    print("❌ Processo do túnel terminou")
                    return False

                time.sleep(0.5)

            print("❌ Timeout ao criar túnel")
            return False

        except Exception as e:
            print(f"❌ Erro: {e}")
            return False


def main():
    """Teste do instalador automático"""
    print("🧪 TESTE DO INSTALADOR AUTOMÁTICO")
    print("=" * 40)

    # Teste 1: Instalação automática
    caminho = instalar_cloudflared_automatico()

    if caminho:
        print(f"\n✅ SUCESSO! Cloudflared disponível em: {caminho}")

        # Teste 2: Criar túnel de teste
        webhook = WebhookManagerComAutoInstall(port=8000)

        if webhook.criar_tunnel():
            print(f"✅ Túnel de teste criado: {webhook.tunnel_url}")

            # Aguardar um pouco para demonstrar
            import time
            print("⏱️  Aguardando 10 segundos...")
            time.sleep(10)

            # Parar túnel
            if webhook.tunnel_process:
                webhook.tunnel_process.terminate()
                print("✅ Túnel de teste finalizado")
        else:
            print("❌ Falha ao criar túnel de teste")
    else:
        print("❌ FALHA na instalação automática")


if __name__ == '__main__':
    main()

# =============================================================================
# 🎯 COMO USAR EM SEUS PROJETOS:
# =============================================================================
#
# 1. INSTALAÇÃO SIMPLES:
#    from auto_installer import instalar_cloudflared_automatico
#    cloudflared_path = instalar_cloudflared_automatico()
#
# 2. WEBHOOK COM AUTO-INSTALL:
#    webhook = WebhookManagerComAutoInstall(port=5000)
#    webhook.criar_tunnel()  # Instala automaticamente se necessário
#
# 3. VERIFICAÇÃO MANUAL:
#    installer = CloudflaredAutoInstaller()
#    if installer.verificar_cloudflared_existente():
#        print("Já instalado!")
#    else:
#        installer.instalar_automatico()
#
# ✅ FUNCIONA EM:
# • Windows (x64, x86)
# • Linux (x64, ARM64, x86)
# • macOS (Intel, Apple Silicon)
#
# 🔧 RECURSOS:
# • Detecção automática do sistema
# • Download da versão mais recente
# • Instalação sem intervenção do usuário
# • Verificação de integridade
# • Limpeza automática de arquivos temporários
#
# =============================================================================
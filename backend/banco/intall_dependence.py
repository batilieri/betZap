#!/usr/bin/env python3
"""
Script para instalar dependências e verificar sistema
Prepara o ambiente para o webhook manager
"""

import subprocess
import sys
import os
import platform


def check_python_version():
    """Verifica versão do Python"""
    version = sys.version_info
    print(f"🐍 Python {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ é necessário")
        return False

    print("✅ Versão do Python compatível")
    return True


def install_packages():
    """Instala pacotes necessários"""
    packages = [
        'flask>=2.0.0',
        'requests>=2.25.0',
        'sqlalchemy>=1.4.0',
        'pandas>=1.3.0'
    ]

    print("\n📦 INSTALANDO DEPENDÊNCIAS...")
    print("-" * 40)

    for package in packages:
        try:
            print(f"📦 Instalando {package}...")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ {package} instalado com sucesso")
            else:
                print(f"❌ Erro ao instalar {package}: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Erro ao instalar {package}: {e}")
            return False

    return True


def verify_installation():
    """Verifica se as dependências foram instaladas"""
    print("\n🔍 VERIFICANDO INSTALAÇÃO...")
    print("-" * 40)

    try:
        import flask
        print(f"✅ Flask {flask.__version__}")
    except ImportError:
        print("❌ Flask não encontrado")
        return False

    try:
        import requests
        print(f"✅ Requests {requests.__version__}")
    except ImportError:
        print("❌ Requests não encontrado")
        return False

    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy {sqlalchemy.__version__}")
    except ImportError:
        print("❌ SQLAlchemy não encontrado")
        return False

    try:
        import pandas
        print(f"✅ Pandas {pandas.__version__}")
    except ImportError:
        print("❌ Pandas não encontrado")
        return False

    return True


def check_cloudflared():
    """Verifica cloudflared"""
    print("\n☁️  VERIFICANDO CLOUDFLARED...")
    print("-" * 40)

    try:
        cmd = 'cloudflared.exe' if platform.system() == 'Windows' else 'cloudflared'
        result = subprocess.run([cmd, '--version'],
                                capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ {version_line}")
            return True
        else:
            print("❌ Cloudflared não encontrado")
            show_cloudflared_guide()
            return False

    except Exception:
        print("❌ Cloudflared não encontrado")
        show_cloudflared_guide()
        return False


def show_cloudflared_guide():
    """Mostra guia de instalação do cloudflared"""
    system = platform.system()
    print("\n📥 COMO INSTALAR CLOUDFLARED:")
    print("-" * 40)

    if system == "Windows":
        print("🪟 WINDOWS:")
        print("1. Acesse: https://github.com/cloudflare/cloudflared/releases/latest")
        print("2. Baixe: cloudflared-ui-amd64.exe")
        print("3. Renomeie para: cloudflared.exe")
        print("4. Coloque na pasta do projeto")

    elif system == "Linux":
        print("🐧 LINUX:")
        print("wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64")
        print("sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared")
        print("sudo chmod +x /usr/local/bin/cloudflared")

    elif system == "Darwin":
        print("🍎 MACOS:")
        print("brew install cloudflared")
        print("# ou baixe manualmente do GitHub")


def create_example_config():
    """Cria arquivo de exemplo de configuração"""
    config_content = """# Configuração do WhatsApp Webhook Manager
# Copie este arquivo para config.py e ajuste conforme necessário

# Configurações do Servidor
SERVER_PORT = 5000
SERVER_HOST = '0.0.0.0'

# Configurações do Banco de Dados
DATABASE_PATH = 'whatsapp_webhook_realtime.db'
DATABASE_BACKUP_DAYS = 30

# Configurações de Limpeza
AUTO_CLEANUP_ENABLED = True
KEEP_MESSAGES_DAYS = 90

# Configurações de Log
LOG_LEVEL = 'INFO'
LOG_FILE = 'webhook_manager.log'

# Configurações de Performance
MAX_BATCH_SIZE = 100
DB_POOL_SIZE = 5
"""

    try:
        with open('config_example.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ Arquivo config_example.py criado")
    except Exception as e:
        print(f"⚠️  Erro ao criar config: {e}")


def check_files():
    """Verifica se os arquivos necessários existem"""
    print("\n📁 VERIFICANDO ARQUIVOS...")
    print("-" * 40)

    required_files = [
        'models_updated.py',
        'database_manager_updated.py',
        'webhook_cloudflare_realtime.py'
    ]

    all_exist = True

    for file in required_files:
        if os.path.exists(file):
            size_kb = round(os.path.getsize(file) / 1024, 1)
            print(f"✅ {file} ({size_kb} KB)")
        else:
            print(f"❌ {file} - ARQUIVO NECESSÁRIO!")
            all_exist = False

    return all_exist


def main():
    """Função principal"""
    print("🛠️  INSTALADOR DE DEPENDÊNCIAS - WHATSAPP WEBHOOK MANAGER")
    print("=" * 60)

    # 1. Verificar Python
    if not check_python_version():
        return False

    # 2. Verificar arquivos
    if not check_files():
        print("\n❌ Arquivos necessários em falta!")
        print("Certifique-se de ter todos os arquivos Python no mesmo diretório")
        return False

    # 3. Instalar dependências
    if not install_packages():
        return False

    # 4. Verificar instalação
    if not verify_installation():
        return False

    # 5. Verificar cloudflared
    cloudflared_ok = check_cloudflared()

    # 6. Criar arquivo de configuração
    create_example_config()

    # 7. Resultado final
    print("\n" + "=" * 60)
    if cloudflared_ok:
        print("🎉 SISTEMA PRONTO PARA USO!")
        print("\n🚀 Para iniciar:")
        print("python webhook_cloudflare_realtime.py")
    else:
        print("⚠️  SISTEMA QUASE PRONTO!")
        print("\n🔧 Instale o cloudflared e execute:")
        print("python webhook_cloudflare_realtime.py")

    print("\n📖 COMANDOS ÚTEIS:")
    print("python webhook_cloudflare_realtime.py --help")
    print("python webhook_cloudflare_realtime.py --port 8000")
    print("python webhook_cloudflare_realtime.py --db meu_banco.db")
    print("=" * 60)

    return True


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Instalação cancelada")
    except Exception as e:
        print(f"\n❌ Erro durante instalação: {e}")
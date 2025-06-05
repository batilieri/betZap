#!/usr/bin/env python3
"""
GUIA COMPLETO: Cloudflare Tunnel Local para APIs Online
Passo a passo para criar túnel gratuito que substitui ngrok
"""

import subprocess
import time
import requests
import json
import os
import platform
from datetime import datetime


class CloudflareTunnelManager:
    """Gerenciador completo do Cloudflare Tunnel"""

    def __init__(self):
        self.sistema = platform.system().lower()
        self.cloudflared_path = self.get_cloudflared_path()
        self.tunnel_url = None
        self.processo_tunnel = None

    def get_cloudflared_path(self):
        """Retorna o caminho do cloudflared baseado no sistema"""
        if self.sistema == "windows":
            return "cloudflared.exe"
        else:
            return "cloudflared"

    def mostrar_introducao(self):
        """Mostra introdução ao Cloudflare Tunnel"""

        print("☁️  CLOUDFLARE TUNNEL - GUIA COMPLETO")
        print("=" * 60)
        print("🎯 OBJETIVO: Criar túnel HTTPS gratuito para APIs online")
        print("🆓 CUSTO: 100% Gratuito - sem limite de tempo")
        print("🚀 VANTAGENS: Mais rápido e estável que ngrok")
        print("=" * 60)

        print("\n📋 O QUE VOCÊ VAI CONSEGUIR:")
        print("   ✅ URL pública HTTPS (ex: https://abc123.trycloudflare.com)")
        print("   ✅ Redireciona para seu localhost:PORTA")
        print("   ✅ Funciona com WhatsApp, webhooks, APIs")
        print("   ✅ SSL certificado automaticamente")
        print("   ✅ Sem cadastro necessário para uso básico")

        print("\n🔄 COMO FUNCIONA:")
        print("   API Online → Cloudflare → Seu localhost")
        print("   Exemplo: WhatsApp → https://abc123.trycloudflare.com → localhost:5000")

    def verificar_cloudflared_instalado(self):
        """Verifica se cloudflared está instalado"""

        print("\n🔍 VERIFICANDO CLOUDFLARED...")

        try:
            result = subprocess.run([self.cloudflared_path, "--version"],
                                    capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ Cloudflared encontrado: {version}")
                return True
            else:
                print("❌ Cloudflared não encontrado")
                return False

        except FileNotFoundError:
            print("❌ Cloudflared não está instalado")
            return False
        except Exception as e:
            print(f"❌ Erro ao verificar cloudflared: {e}")
            return False

    def instalar_cloudflared(self):
        """Guia de instalação do cloudflared"""

        print("\n📦 INSTALANDO CLOUDFLARED...")
        print("=" * 40)

        if self.sistema == "windows":
            self.instalar_windows()
        elif self.sistema == "linux":
            self.instalar_linux()
        elif self.sistema == "darwin":  # macOS
            self.instalar_macos()
        else:
            print("❌ Sistema não suportado")
            return False

        # Verificar se instalação funcionou
        time.sleep(3)
        return self.verificar_cloudflared_instalado()

    def instalar_windows(self):
        """Instalação no Windows"""

        print("🪟 INSTALAÇÃO NO WINDOWS:")
        print("=" * 30)

        print("📋 OPÇÃO 1 - Download Manual (Recomendado):")
        print("   1. Acesse: https://github.com/cloudflare/cloudflared/releases/latest")
        print("   2. Baixe: cloudflared-windows-amd64.exe")
        print("   3. Renomeie para: cloudflared.exe")
        print("   4. Coloque em uma pasta no PATH ou pasta atual")

        print("\n📋 OPÇÃO 2 - Via Chocolatey:")
        print("   choco install cloudflared")

        print("\n📋 OPÇÃO 3 - Via Scoop:")
        print("   scoop install cloudflared")

        print("\n📋 OPÇÃO 4 - Download Automático:")
        resposta = input("Deseja que eu baixe automaticamente? (s/n): ").lower()

        if resposta == 's':
            self.baixar_cloudflared_windows()

    def baixar_cloudflared_windows(self):
        """Baixa cloudflared automaticamente no Windows"""

        print("⬇️  Baixando cloudflared para Windows...")

        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

        try:
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))

            with open('cloudflared.exe', 'wb') as file:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r📊 Progresso: {percent:.1f}%", end="", flush=True)

            print(f"\n✅ Cloudflared baixado com sucesso!")
            print(f"📁 Localização: {os.path.abspath('cloudflared.exe')}")

        except Exception as e:
            print(f"\n❌ Erro ao baixar: {e}")
            print("💡 Baixe manualmente do GitHub")

    def instalar_linux(self):
        """Instalação no Linux"""

        print("🐧 INSTALAÇÃO NO LINUX:")
        print("=" * 30)

        # Detectar distribuição
        try:
            with open('/etc/os-release', 'r') as f:
                os_info = f.read()

            if 'ubuntu' in os_info.lower() or 'debian' in os_info.lower():
                self.instalar_ubuntu_debian()
            elif 'centos' in os_info.lower() or 'rhel' in os_info.lower():
                self.instalar_centos_rhel()
            else:
                self.instalar_linux_generic()

        except:
            self.instalar_linux_generic()

    def instalar_ubuntu_debian(self):
        """Instalação Ubuntu/Debian"""

        print("📋 UBUNTU/DEBIAN:")

        comandos = [
            "# Adicionar repositório Cloudflare",
            "curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null",
            "echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main' | sudo tee /etc/apt/sources.list.d/cloudflared.list",
            "sudo apt-get update",
            "sudo apt-get install cloudflared"
        ]

        print("\n🔧 Execute estes comandos:")
        for cmd in comandos:
            print(f"   {cmd}")

        print("\n📋 OU download direto:")
        print("   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64")
        print("   sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared")
        print("   sudo chmod +x /usr/local/bin/cloudflared")

        # Tentar instalação automática
        resposta = input("\nDeseja tentar instalação automática? (s/n): ").lower()
        if resposta == 's':
            self.instalar_linux_automatico()

    def instalar_linux_automatico(self):
        """Instalação automática no Linux"""

        print("⬇️  Instalando cloudflared automaticamente...")

        try:
            # Download
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
            subprocess.run(["wget", url, "-O", "cloudflared"], check=True)

            # Tornar executável
            subprocess.run(["chmod", "+x", "cloudflared"], check=True)

            print("✅ Cloudflared baixado e configurado!")
            print("📁 Localização: ./cloudflared")

            # Tentar mover para /usr/local/bin
            try:
                subprocess.run(["sudo", "mv", "cloudflared", "/usr/local/bin/"], check=True)
                print("✅ Movido para /usr/local/bin/cloudflared")
                self.cloudflared_path = "cloudflared"
            except:
                print("⚠️  Mantido na pasta atual como ./cloudflared")
                self.cloudflared_path = "./cloudflared"

        except Exception as e:
            print(f"❌ Erro na instalação automática: {e}")
            print("💡 Instale manualmente seguindo os comandos acima")

    def instalar_macos(self):
        """Instalação no macOS"""

        print("🍎 INSTALAÇÃO NO MACOS:")
        print("=" * 30)

        print("📋 OPÇÃO 1 - Via Homebrew (Recomendado):")
        print("   brew install cloudflared")

        print("\n📋 OPÇÃO 2 - Download Manual:")
        print(
            "   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz | tar -xzf -")
        print("   sudo mv cloudflared /usr/local/bin")
        print("   sudo chmod +x /usr/local/bin/cloudflared")

        # Tentar via Homebrew
        resposta = input("\nDeseja tentar instalação via Homebrew? (s/n): ").lower()
        if resposta == 's':
            try:
                subprocess.run(["brew", "install", "cloudflared"], check=True)
                print("✅ Instalado via Homebrew!")
            except:
                print("❌ Erro com Homebrew. Instale manualmente.")

    def criar_tunnel_temporario(self, porta_local=5000):
        """Cria túnel temporário (sem login)"""

        print(f"\n🚀 CRIANDO TÚNEL TEMPORÁRIO...")
        print("=" * 40)
        print(f"🔌 Porta local: {porta_local}")
        print("⏱️  Tipo: Temporário (sem login)")
        print("🔗 URL: Será gerada automaticamente")

        try:
            # Comando para túnel temporário
            comando = [
                self.cloudflared_path,
                "tunnel",
                "--url", f"http://localhost:{porta_local}"
            ]

            print(f"\n📡 Executando: {' '.join(comando)}")
            print("⏳ Aguardando URL...")

            # Iniciar processo
            self.processo_tunnel = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Aguardar URL
            url_encontrada = False
            timeout = 30
            inicio = time.time()

            while not url_encontrada and (time.time() - inicio) < timeout:
                linha = self.processo_tunnel.stdout.readline()

                if linha:
                    print(f"📊 Log: {linha.strip()}")

                    # Procurar URL do túnel
                    if 'trycloudflare.com' in linha:
                        # Extrair URL
                        palavras = linha.split()
                        for palavra in palavras:
                            if 'https://' in palavra and 'trycloudflare.com' in palavra:
                                self.tunnel_url = palavra.strip()
                                url_encontrada = True
                                break

                # Verificar se processo ainda está rodando
                if self.processo_tunnel.poll() is not None:
                    print("❌ Processo do túnel terminou inesperadamente")
                    return False

                time.sleep(0.5)

            if url_encontrada:
                print(f"\n🎉 TÚNEL CRIADO COM SUCESSO!")
                print("=" * 40)
                print(f"🌐 URL Pública: {self.tunnel_url}")
                print(f"🔗 Webhook URL: {self.tunnel_url}/webhook")
                print(f"🏠 Redirecionando para: http://localhost:{porta_local}")
                return True
            else:
                print("❌ Timeout: Não foi possível obter URL do túnel")
                self.parar_tunnel()
                return False

        except Exception as e:
            print(f"❌ Erro ao criar túnel: {e}")
            return False

    def criar_tunnel_nomeado(self, nome_tunnel, porta_local=5000):
        """Cria túnel nomeado (requer login)"""

        print(f"\n🏷️  CRIANDO TÚNEL NOMEADO...")
        print("=" * 40)
        print(f"📛 Nome: {nome_tunnel}")
        print(f"🔌 Porta: {porta_local}")
        print("🔐 Requer: Login na Cloudflare")

        # Verificar se está logado
        if not self.verificar_login():
            print("❌ É necessário fazer login primeiro")
            self.fazer_login()
            return False

        try:
            # Criar túnel
            comando_criar = [
                self.cloudflared_path,
                "tunnel", "create", nome_tunnel
            ]

            result = subprocess.run(comando_criar, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ Túnel '{nome_tunnel}' criado!")
            else:
                print(f"⚠️  Túnel pode já existir: {result.stderr}")

            # Configurar rota
            comando_rota = [
                self.cloudflared_path,
                "tunnel", "route", "dns", nome_tunnel, f"{nome_tunnel}.exemplo.com"
            ]

            # Executar túnel
            comando_run = [
                self.cloudflared_path,
                "tunnel", "run", "--url", f"http://localhost:{porta_local}", nome_tunnel
            ]

            print(f"🚀 Iniciando túnel nomeado...")
            self.processo_tunnel = subprocess.Popen(comando_run)

            return True

        except Exception as e:
            print(f"❌ Erro ao criar túnel nomeado: {e}")
            return False

    def verificar_login(self):
        """Verifica se está logado na Cloudflare"""

        try:
            result = subprocess.run([self.cloudflared_path, "tunnel", "list"],
                                    capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def fazer_login(self):
        """Guia para fazer login na Cloudflare"""

        print("\n🔐 LOGIN NA CLOUDFLARE:")
        print("=" * 30)
        print("1. Execute: cloudflared tunnel login")
        print("2. Será aberto um navegador")
        print("3. Faça login na sua conta Cloudflare")
        print("4. Autorize o cloudflared")
        print("5. Volte ao terminal")

        input("Pressione Enter após fazer login...")

    def testar_tunnel(self):
        """Testa se o túnel está funcionando"""

        if not self.tunnel_url:
            print("❌ Nenhum túnel ativo para testar")
            return False

        print(f"\n🧪 TESTANDO TÚNEL...")
        print("=" * 30)
        print(f"🔗 URL: {self.tunnel_url}")

        try:
            # Teste básico
            response = requests.get(self.tunnel_url, timeout=10)

            print(f"📊 Status Code: {response.status_code}")
            print(f"⏱️  Tempo resposta: {response.elapsed.total_seconds():.2f}s")

            if response.status_code in [200, 404]:  # 404 é OK se não há servidor
                print("✅ Túnel funcionando!")

                # Teste específico para webhook
                webhook_url = f"{self.tunnel_url}/status"
                try:
                    resp_webhook = requests.get(webhook_url, timeout=5)
                    if resp_webhook.status_code == 200:
                        print("✅ Webhook endpoint acessível!")
                    else:
                        print("⚠️  Webhook endpoint não encontrado (normal se servidor não está rodando)")
                except:
                    print("⚠️  Servidor local não está respondendo")

                return True
            else:
                print(f"❌ Túnel retornou erro: {response.status_code}")
                return False

        except requests.exceptions.SSLError:
            print("❌ Erro de SSL")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ Não foi possível conectar")
            return False
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
            return False

    def parar_tunnel(self):
        """Para o túnel ativo"""

        if self.processo_tunnel:
            print("\n🛑 Parando túnel...")
            self.processo_tunnel.terminate()

            try:
                self.processo_tunnel.wait(timeout=5)
                print("✅ Túnel parado")
            except subprocess.TimeoutExpired:
                self.processo_tunnel.kill()
                print("✅ Túnel forçadamente parado")

            self.processo_tunnel = None
            self.tunnel_url = None
        else:
            print("ℹ️  Nenhum túnel ativo")

    def monitorar_tunnel(self):
        """Monitora o túnel em tempo real"""

        if not self.processo_tunnel:
            print("❌ Nenhum túnel ativo para monitorar")
            return

        print(f"\n📊 MONITORANDO TÚNEL: {self.tunnel_url}")
        print("=" * 50)
        print("💡 Pressione Ctrl+C para parar")
        print("=" * 50)

        try:
            while self.processo_tunnel.poll() is None:
                # Verificar status
                try:
                    response = requests.get(self.tunnel_url, timeout=5)
                    status = "🟢 ONLINE" if response.status_code < 400 else "🟡 PROBLEMAS"
                    tempo_resposta = response.elapsed.total_seconds()

                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"\r{status} | {timestamp} | Resposta: {tempo_resposta:.2f}s",
                          end="", flush=True)

                except:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"\r🔴 OFFLINE | {timestamp}", end="", flush=True)

                time.sleep(5)

        except KeyboardInterrupt:
            print(f"\n👋 Monitoramento interrompido")
            self.parar_tunnel()

    def mostrar_resumo_final(self):
        """Mostra resumo final da configuração"""

        if not self.tunnel_url:
            print("❌ Nenhum túnel ativo")
            return

        print("\n" + "=" * 60)
        print("🎉 CLOUDFLARE TUNNEL CONFIGURADO COM SUCESSO!")
        print("=" * 60)
        print(f"🌐 URL Pública: {self.tunnel_url}")
        print(f"📡 Para Webhook: {self.tunnel_url}/webhook")
        print(f"🔧 Para API: {self.tunnel_url}/api/endpoint")
        print(f"📊 Status: {self.tunnel_url}/status")

        print(f"\n📋 CONFIGURAÇÃO PARA WHATSAPP:")
        print(f"   URL do Webhook: {self.tunnel_url}/webhook")
        print(f"   Token de Verificação: SEU_TOKEN_AQUI")

        print(f"\n🧪 TESTES RÁPIDOS:")
        print(f"   # Teste básico:")
        print(f"   curl {self.tunnel_url}")
        print(f"   ")
        print(f"   # Teste webhook:")
        print(f"   curl {self.tunnel_url}/webhook")

        print(f"\n💡 DICAS:")
        print(f"   • URL muda a cada restart (túnel temporário)")
        print(f"   • Para URL fixa, use túnel nomeado")
        print(f"   • Túnel fica ativo enquanto processo roda")
        print(f"   • Use Ctrl+C para parar")

        print("=" * 60)


def main():
    """Função principal do guia"""

    manager = CloudflareTunnelManager()

    # Introdução
    manager.mostrar_introducao()

    # Menu principal
    while True:
        print("\n📋 MENU CLOUDFLARE TUNNEL:")
        print("1. 🔍 Verificar instalação")
        print("2. 📦 Instalar cloudflared")
        print("3. 🚀 Criar túnel temporário")
        print("4. 🏷️  Criar túnel nomeado")
        print("5. 🧪 Testar túnel atual")
        print("6. 📊 Monitorar túnel")
        print("7. 🛑 Parar túnel")
        print("8. 📋 Mostrar resumo")
        print("9. ❌ Sair")

        escolha = input("\nDigite sua escolha (1-9): ").strip()

        if escolha == "1":
            manager.verificar_cloudflared_instalado()

        elif escolha == "2":
            if not manager.verificar_cloudflared_instalado():
                manager.instalar_cloudflared()
            else:
                print("✅ Cloudflared já está instalado!")

        elif escolha == "3":
            if not manager.verificar_cloudflared_instalado():
                print("❌ Instale cloudflared primeiro (opção 2)")
                continue

            porta = input("Digite a porta local (padrão 5000): ").strip()
            porta = int(porta) if porta.isdigit() else 5000

            if manager.criar_tunnel_temporario(porta):
                manager.mostrar_resumo_final()

        elif escolha == "4":
            if not manager.verificar_cloudflared_instalado():
                print("❌ Instale cloudflared primeiro (opção 2)")
                continue

            nome = input("Digite o nome do túnel: ").strip()
            porta = input("Digite a porta local (padrão 5000): ").strip()
            porta = int(porta) if porta.isdigit() else 5000

            manager.criar_tunnel_nomeado(nome, porta)

        elif escolha == "5":
            manager.testar_tunnel()

        elif escolha == "6":
            manager.monitorar_tunnel()

        elif escolha == "7":
            manager.parar_tunnel()

        elif escolha == "8":
            manager.mostrar_resumo_final()

        elif escolha == "9":
            manager.parar_tunnel()
            print("👋 Saindo...")
            break

        else:
            print("❌ Opção inválida!")


if __name__ == '__main__':
    main()

# =============================================================================
# ☁️  CLOUDFLARE TUNNEL - RESUMO RÁPIDO:
# =============================================================================
#
# 🎯 OBJETIVO: Substituir ngrok com solução gratuita da Cloudflare
#
# 📦 INSTALAÇÃO:
# • Windows: Baixar cloudflared.exe do GitHub
# • Linux: wget + chmod ou via package manager
# • macOS: brew install cloudflared
#
# 🚀 USO BÁSICO:
# cloudflared tunnel --url http://localhost:5000
#
# ✅ VANTAGENS:
# • 100% gratuito
# • Mais rápido que ngrok
# • SSL automático
# • Sem limite de tempo
# • URLs https://abc123.trycloudflare.com
#
# 📱 PARA WHATSAPP:
# • URL: https://abc123.trycloudflare.com/webhook
# • Funcionamento idêntico ao ngrok
# • Melhor performance
#
# =============================================================================
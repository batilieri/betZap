#!/usr/bin/env python3
"""
Monitor de Conexão WhatsApp W-API
Monitora status de conexão/desconexão e configura webhooks automaticamente
"""

import requests
import json
import time
import os
from datetime import datetime
from enum import Enum


class StatusConexao(Enum):
    CONECTADO = "conectado"
    DESCONECTADO = "desconectado"
    ERRO = "erro"
    DESCONHECIDO = "desconhecido"


class MonitorConexaoWAPI:
    def __init__(self, instance_id=None, bearer_token=None, webhook_id=None):
        self.instance_id = instance_id
        self.bearer_token = bearer_token
        self.webhook_id = webhook_id
        self.webhook_url = f"https://webhook.site/{webhook_id}" if webhook_id else None
        self.base_url = "https://api.w-api.app/v1"
        self.status_atual = StatusConexao.DESCONHECIDO
        self.ultimo_check = None
        self.ultimo_erro = None
        self.historico_conexao = []

    def testar_configuracao_basica(self):
        """Testa se a configuração básica está funcionando"""

        print("\n🧪 TESTANDO CONFIGURAÇÃO")
        print("=" * 30)

        # Teste 1: Verificar se a API responde
        try:
            url = "https://api.w-api.app/v1/instance/list"
            headers = {'Authorization': f'Bearer {self.bearer_token}'}

            print("🔍 Testando conectividade com API...")
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                print("✅ API respondendo normalmente")

                # Verificar se tem instâncias
                try:
                    data = response.json()
                    if not data.get('error', True):
                        instances = data.get('data', [])
                        print(f"📱 {len(instances)} instância(s) encontrada(s)")

                        # Verificar se nossa instância existe
                        nossa_instancia = None
                        for inst in instances:
                            if inst.get('instanceId') == self.instance_id:
                                nossa_instancia = inst
                                break

                        if nossa_instancia:
                            print(f"✅ Instância {self.instance_id} encontrada")
                            print(f"📊 Status: {nossa_instancia}")
                        else:
                            print(f"❌ Instância {self.instance_id} NÃO encontrada")
                            print("💡 Verifique se o Instance ID está correto")
                    else:
                        print(f"❌ Erro na API: {data}")
                except:
                    print("⚠️ Resposta da API não é JSON válido")

            elif response.status_code == 401:
                print("❌ Token de autorização INVÁLIDO")
                print("💡 Verifique se o Bearer Token está correto")
                return False
            else:
                print(f"❌ API retornou erro: {response.status_code}")
                print(f"📋 Resposta: {response.text[:200]}")
                return False

        except requests.Timeout:
            print("❌ TIMEOUT na conexão com a API")
            print("💡 Verifique sua conexão com a internet")
            return False
        except requests.ConnectionError:
            print("❌ ERRO DE CONEXÃO com a API")
            print("💡 Verifique se a URL da API está correta")
            return False
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return False

        return True

    def carregar_configuracao(self):
        """Carrega configuração de variáveis de ambiente ou solicita"""

        # Tentar variáveis de ambiente primeiro
        self.instance_id = self.instance_id or os.getenv('WAPI_INSTANCE_ID')
        self.bearer_token = self.bearer_token or os.getenv('WAPI_BEARER_TOKEN')
        self.webhook_id = self.webhook_id or os.getenv('WAPI_WEBHOOK_ID')

        # Se não tem configuração completa, solicitar
        if not all([self.instance_id, self.bearer_token, self.webhook_id]):
            print("🔧 CONFIGURAÇÃO W-API")
            print("=" * 30)

            if not self.instance_id:
                self.instance_id = input("📱 Instance ID: ").strip()

            if not self.bearer_token:
                self.bearer_token = input("🔑 Bearer Token: ").strip()

            if not self.webhook_id:
                webhook_input = input("🔗 Webhook URL ou ID: ").strip()
                self.webhook_id = self.extrair_webhook_id(webhook_input)

        # Configurar URL do webhook
        if self.webhook_id:
            self.webhook_url = f"https://webhook.site/{self.webhook_id}"

        return all([self.instance_id, self.bearer_token, self.webhook_id])

    def extrair_webhook_id(self, webhook_input):
        """Extrai ID do webhook de URL ou retorna o próprio ID"""
        if not webhook_input:
            return None

        webhook_id = webhook_input.replace('https://webhook.site/', '')
        webhook_id = webhook_id.replace('http://webhook.site/', '')
        return webhook_id.strip()

    def configurar_webhook_conexao(self):
        """Configura webhook para eventos de conexão"""

        url = f"{self.base_url}/webhook/update-webhook-connected"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        params = {
            'instanceId': self.instance_id
        }
        data = {
            'value': self.webhook_url
        }

        try:
            response = requests.put(url, headers=headers, params=params, json=data)

            if response.status_code == 200:
                result = response.json()
                if not result.get('error', True):
                    print("✅ Webhook de CONEXÃO configurado com sucesso!")
                    return True
                else:
                    print(f"❌ Erro ao configurar webhook de conexão: {result.get('message', 'Erro desconhecido')}")
                    return False
            else:
                print(f"❌ Erro HTTP ao configurar webhook de conexão: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Erro ao configurar webhook de conexão: {e}")
            return False

    def configurar_webhook_desconexao(self):
        """Configura webhook para eventos de desconexão"""

        url = f"{self.base_url}/webhook/update-webhook-disconnected"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.bearer_token}'
        }
        params = {
            'instanceId': self.instance_id
        }
        data = {
            'value': self.webhook_url
        }

        try:
            response = requests.put(url, headers=headers, params=params, json=data)

            if response.status_code == 200:
                result = response.json()
                if not result.get('error', True):
                    print("✅ Webhook de DESCONEXÃO configurado com sucesso!")
                    return True
                else:
                    print(f"❌ Erro ao configurar webhook de desconexão: {result.get('message', 'Erro desconhecido')}")
                    return False
            else:
                print(f"❌ Erro HTTP ao configurar webhook de desconexão: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Erro ao configurar webhook de desconexão: {e}")
            return False

    def verificar_status_instancia(self):
        """Verifica o status atual da instância via API"""

        url = f"{self.base_url}/instance/status"
        headers = {
            'Authorization': f'Bearer {self.bearer_token}'
        }
        params = {
            'instanceId': self.instance_id
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)

            print(f"🔍 Debug API - Status Code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"🔍 Debug API - Response: {json.dumps(result, indent=2)}")

                # Interpretar resposta da API
                if not result.get('error', True):
                    status_info = result.get('data', {})
                    connected = status_info.get('connected', False)

                    if connected:
                        return StatusConexao.CONECTADO, status_info
                    else:
                        return StatusConexao.DESCONECTADO, status_info
                else:
                    return StatusConexao.ERRO, result
            elif response.status_code == 401:
                return StatusConexao.ERRO, {'error': 'Token de autorização inválido', 'code': 401}
            elif response.status_code == 404:
                return StatusConexao.ERRO, {'error': 'Instância não encontrada', 'code': 404}
            else:
                try:
                    error_data = response.json()
                    return StatusConexao.ERRO, {'error': f'HTTP {response.status_code}', 'details': error_data}
                except:
                    return StatusConexao.ERRO, {'error': f'HTTP {response.status_code}', 'text': response.text[:200]}

        except requests.Timeout:
            return StatusConexao.ERRO, {'error': 'Timeout na conexão com a API'}
        except requests.ConnectionError:
            return StatusConexao.ERRO, {'error': 'Erro de conexão com a API'}
        except Exception as e:
            return StatusConexao.ERRO, {'error': str(e)}

    def buscar_eventos_webhook(self):
        """Busca eventos de conexão/desconexão no webhook"""

        try:
            url = f"https://webhook.site/token/{self.webhook_id}/requests"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                eventos = []

                for request in data.get('data', []):
                    content = request.get('content')
                    timestamp = request.get('created_at')

                    if content:
                        try:
                            event_data = json.loads(content)

                            # Identificar tipo de evento
                            if self.eh_evento_conexao(event_data):
                                eventos.append({
                                    'tipo': 'conexao',
                                    'timestamp': timestamp,
                                    'data': event_data
                                })
                            elif self.eh_evento_desconexao(event_data):
                                eventos.append({
                                    'tipo': 'desconexao',
                                    'timestamp': timestamp,
                                    'data': event_data
                                })

                        except json.JSONDecodeError:
                            pass

                return eventos
            else:
                return []

        except Exception as e:
            print(f"⚠️ Erro ao buscar eventos do webhook: {e}")
            return []

    def eh_evento_conexao(self, data):
        """Verifica se é evento de conexão"""
        return any([
            data.get('event') == 'connected',
            data.get('type') == 'connected',
            data.get('status') == 'connected',
            'connected' in str(data).lower() and 'true' in str(data).lower()
        ])

    def eh_evento_desconexao(self, data):
        """Verifica se é evento de desconexão"""
        return any([
            data.get('event') == 'disconnected',
            data.get('type') == 'disconnected',
            data.get('status') == 'disconnected',
            'disconnect' in str(data).lower()
        ])

    def registrar_mudanca_status(self, novo_status, detalhes=None):
        """Registra mudança de status no histórico"""

        if novo_status != self.status_atual:
            mudanca = {
                'timestamp': datetime.now(),
                'status_anterior': self.status_atual.value,
                'status_novo': novo_status.value,
                'detalhes': detalhes
            }

            self.historico_conexao.append(mudanca)
            self.status_atual = novo_status

            # Exibir mudança
            self.exibir_mudanca_status(mudanca)

    def exibir_mudanca_status(self, mudanca):
        """Exibe mudança de status formatada"""

        timestamp = mudanca['timestamp'].strftime('%H:%M:%S')
        status_anterior = mudanca['status_anterior']
        status_novo = mudanca['status_novo']

        print('\n' + '🔄' * 50)
        print(f'📱 MUDANÇA DE STATUS - {timestamp}')
        print('🔄' * 50)

        # Ícones para status
        icones = {
            'conectado': '🟢',
            'desconectado': '🔴',
            'erro': '❌',
            'desconhecido': '⚪'
        }

        print(f"{icones.get(status_anterior, '⚪')} DE: {status_anterior.upper()}")
        print(f"{icones.get(status_novo, '⚪')} PARA: {status_novo.upper()}")

        if mudanca.get('detalhes'):
            print(f"📋 Detalhes: {mudanca['detalhes']}")

        print('🔄' * 50 + '\n')

    def exibir_status_atual(self):
        """Exibe status atual formatado"""

        icones = {
            StatusConexao.CONECTADO: '🟢',
            StatusConexao.DESCONECTADO: '🔴',
            StatusConexao.ERRO: '❌',
            StatusConexao.DESCONHECIDO: '⚪'
        }

        icone = icones.get(self.status_atual, '⚪')
        status_texto = self.status_atual.value.upper()

        print(f"\n{icone} STATUS: {status_texto}")

        if self.ultimo_check:
            tempo_check = self.ultimo_check.strftime('%H:%M:%S')
            print(f"🕐 Última verificação: {tempo_check}")

    def monitorar_conexao(self, intervalo=30):
        """Monitora conexão em tempo real"""

        print(f"\n🚀 MONITOR DE CONEXÃO INICIADO")
        print("=" * 40)
        print(f"📱 Instância: {self.instance_id}")
        print(f"🔗 Webhook: {self.webhook_id}")
        print(f"⏱️ Intervalo: {intervalo}s")
        print("💡 Pressione Ctrl+C para parar\n")

        try:
            while True:
                # Verificar status via API
                status, detalhes = self.verificar_status_instancia()
                self.ultimo_check = datetime.now()

                # Registrar mudança se houver
                self.registrar_mudanca_status(status, detalhes)

                # Exibir status atual
                self.exibir_status_atual()

                # Verificar eventos do webhook
                eventos = self.buscar_eventos_webhook()
                if eventos:
                    print(f"📨 {len(eventos)} eventos encontrados no webhook")

                time.sleep(intervalo)

        except KeyboardInterrupt:
            print(f"\n👋 MONITORAMENTO PARADO!")
            self.exibir_historico()

    def exibir_historico(self):
        """Exibe histórico de mudanças"""

        if not self.historico_conexao:
            print("📊 Nenhuma mudança de status registrada.")
            return

        print(f"\n📊 HISTÓRICO DE CONEXÃO ({len(self.historico_conexao)} mudanças)")
        print("=" * 50)

        for i, mudanca in enumerate(self.historico_conexao[-10:], 1):  # Últimas 10
            timestamp = mudanca['timestamp'].strftime('%H:%M:%S')
            status_novo = mudanca['status_novo']

            icones = {
                'conectado': '🟢',
                'desconectado': '🔴',
                'erro': '❌',
                'desconhecido': '⚪'
            }

            icone = icones.get(status_novo, '⚪')
            print(f"{i:2}. {timestamp} - {icone} {status_novo.upper()}")

    def configurar_webhooks_completo(self):
        """Configura ambos os webhooks (conexão e desconexão)"""

        print("\n🔧 CONFIGURANDO WEBHOOKS")
        print("=" * 30)

        sucesso_conexao = self.configurar_webhook_conexao()
        sucesso_desconexao = self.configurar_webhook_desconexao()

        if sucesso_conexao and sucesso_desconexao:
            print("\n✅ Todos os webhooks configurados com sucesso!")
            return True
        else:
            print("\n⚠️ Alguns webhooks falharam na configuração.")
            return False

    def executar(self):
        """Executa o monitor completo"""

        print("🔗 MONITOR DE CONEXÃO W-API")
        print("=" * 40)

        # Carregar configuração
        if not self.carregar_configuracao():
            print("❌ Configuração incompleta!")
            return

        print(f"\n✅ Configuração carregada:")
        print(f"📱 Instance ID: {self.instance_id}")
        print(f"🔗 Webhook: {self.webhook_url}")

        # Testar configuração básica primeiro
        if not self.testar_configuracao_basica():
            print("\n❌ Problemas na configuração básica!")
            print("💡 Corrija os problemas acima antes de continuar")
            return

        # Configurar webhooks
        if self.configurar_webhooks_completo():
            # Verificar status inicial
            status, detalhes = self.verificar_status_instancia()
            self.registrar_mudanca_status(status, detalhes)
            self.ultimo_check = datetime.now()

            print(f"\n📊 Status inicial:")
            self.exibir_status_atual()

            # Se há erro no status inicial, explicar possíveis causas
            if status == StatusConexao.ERRO:
                print("\n🔍 POSSÍVEIS CAUSAS DO ERRO:")
                print("1. 📱 WhatsApp não está conectado (precisa escanear QR Code)")
                print("2. 🔄 Instância foi pausada ou desativada")
                print("3. ⏱️ Timeout de inatividade")
                print("4. 🔧 Problemas de configuração na W-API")
                print("5. 🌐 Problemas de conectividade")

            # Perguntar se quer monitorar continuamente
            continuar = input("\n❓ Iniciar monitoramento contínuo? (s/n): ").lower()

            if continuar.startswith('s') or continuar == '':
                self.monitorar_conexao()
        else:
            print("❌ Falha na configuração dos webhooks!")


def main():
    """Função principal"""

    # Você pode definir valores padrão aqui
    monitor = MonitorConexaoWAPI()
    monitor.executar()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Monitor encerrado!")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

# ========================================
# CONFIGURAÇÃO VIA VARIÁVEIS DE AMBIENTE:
# ========================================
#
# export WAPI_INSTANCE_ID=sua_instancia
# export WAPI_BEARER_TOKEN=seu_token
# export WAPI_WEBHOOK_ID=seu_webhook_id
# python monitor_conexao.py
#
# ========================================
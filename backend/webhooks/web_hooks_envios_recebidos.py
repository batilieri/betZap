#!/usr/bin/env python3
"""
Debug Webhook Melhorado - Tempo Real Funcional
Corrige problemas de monitoramento e adiciona melhor análise
"""

import requests
import json
import time
from datetime import datetime
import hashlib

# ✅ WEBHOOK CORRETO
WEBHOOK_ID = '0e6e92fd-c357-44e4-b1e5-067d6ae4cd0d'


class WebhookDebugMelhorado:
    def __init__(self, webhook_id):
        self.webhook_id = webhook_id
        self.url_api = f"https://webhook.site/token/{webhook_id}/requests"
        self.webhook_url = f"https://webhook.site/{webhook_id}"
        self.requisicoes_processadas = set()
        self.ultima_verificacao = None

    def testar_conectividade(self):
        """Testa conectividade com webhook.site"""
        print("🔌 TESTANDO CONECTIVIDADE")
        print("=" * 40)

        try:
            # Teste 1: URL principal do webhook
            print(f"🔗 Testando URL principal: {self.webhook_url}")
            response = requests.get(self.webhook_url, timeout=10)
            print(f"   Status: {response.status_code}")
            print(f"   ✅ Webhook acessível!" if response.status_code == 200 else "   ❌ Webhook inacessível")

            # Teste 2: API de requisições
            print(f"\n📡 Testando API: {self.url_api}")
            response = requests.get(self.url_api, timeout=10)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                total_reqs = len(data.get('data', []))
                print(f"   ✅ API funcionando! Total de requisições: {total_reqs}")
                return True
            else:
                print(f"   ❌ API não responde corretamente")
                return False

        except Exception as e:
            print(f"❌ Erro de conectividade: {e}")
            return False

    def buscar_requisicoes_novas(self):
        """Busca apenas requisições novas (mais eficiente)"""
        try:
            response = requests.get(self.url_api, timeout=5)

            if response.status_code != 200:
                print(f"⚠️ API retornou status {response.status_code}")
                return []

            data = response.json()
            todas_requisicoes = data.get('data', [])

            # Filtrar apenas requisições novas
            requisicoes_novas = []

            for req in todas_requisicoes:
                # Criar ID único para a requisição
                req_id = self.criar_id_requisicao(req)

                if req_id not in self.requisicoes_processadas:
                    self.requisicoes_processadas.add(req_id)
                    requisicoes_novas.append(req)

            return requisicoes_novas

        except requests.RequestException as e:
            print(f"⚠️ Erro de rede: {e}")
            return []
        except Exception as e:
            print(f"⚠️ Erro inesperado: {e}")
            return []

    def criar_id_requisicao(self, req):
        """Cria ID único para requisição baseado em múltiplos fatores"""
        # Usar UUID se disponível
        if 'uuid' in req and req['uuid']:
            return req['uuid']

        # Caso contrário, criar hash baseado no conteúdo
        elementos_id = [
            str(req.get('created_at', '')),
            str(req.get('ip', '')),
            str(req.get('user_agent', '')),
            str(req.get('content', ''))[:100],  # Primeiros 100 chars
            str(req.get('method', '')),
            str(req.get('url', ''))
        ]

        texto_id = '|'.join(elementos_id)
        return hashlib.md5(texto_id.encode()).hexdigest()

    def analisar_requisicao_completa(self, req, numero):
        """Análise mais detalhada e organizada"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"\n🆕 NOVA REQUISIÇÃO #{numero} - {timestamp}")
        print("=" * 50)

        # 1. Informações básicas
        print("📋 INFORMAÇÕES BÁSICAS:")
        campos_basicos = ['created_at', 'method', 'ip', 'user_agent']
        for campo in campos_basicos:
            valor = req.get(campo, 'N/A')
            print(f"   {campo}: {valor}")

        # 2. Análise do conteúdo (foco principal)
        print(f"\n💬 ANÁLISE DO CONTEÚDO:")
        content = req.get('content')

        if content is None:
            print("   ❌ Conteúdo é NULL")
            self.buscar_conteudo_alternativo(req)
        elif content == '':
            print("   ❌ Conteúdo é string vazia")
            self.buscar_conteudo_alternativo(req)
        else:
            print(f"   ✅ Conteúdo encontrado!")
            print(f"   📏 Tamanho: {len(str(content))} caracteres")
            print(f"   🔍 Tipo: {type(content)}")

            # Tentar interpretar como JSON
            self.interpretar_conteudo(content)

        # 3. Headers e outros dados
        self.analisar_headers_e_extras(req)

        print("=" * 50)

    def buscar_conteudo_alternativo(self, req):
        """Busca conteúdo em campos alternativos"""
        print("   🔍 PROCURANDO EM CAMPOS ALTERNATIVOS:")

        campos_alternativos = [
            'body', 'text', 'payload', 'data', 'message',
            'json', 'raw', 'form', 'query'
        ]

        encontrou_algo = False

        for campo in campos_alternativos:
            if campo in req and req[campo]:
                print(f"   ✅ {campo}: {req[campo]}")
                encontrou_algo = True
                # Tentar interpretar este conteúdo
                self.interpretar_conteudo(req[campo])

        if not encontrou_algo:
            print("   ❌ Nenhum conteúdo encontrado em campos alternativos")

        # Mostrar TODOS os campos disponíveis
        print(f"\n   📋 TODOS OS CAMPOS DISPONÍVEIS:")
        for key, value in req.items():
            tamanho = len(str(value)) if value else 0
            print(f"      {key}: {type(value)} (tamanho: {tamanho})")

    def interpretar_conteudo(self, content):
        """Interpreta o conteúdo de forma mais robusta"""
        print(f"   🧪 INTERPRETANDO CONTEÚDO:")

        # Se for string, tentar JSON
        if isinstance(content, str):
            if content.strip():
                try:
                    json_data = json.loads(content)
                    print(f"   ✅ JSON válido encontrado!")
                    print(f"   📋 Estrutura JSON:")
                    print(json.dumps(json_data, indent=6, ensure_ascii=False))

                    # Verificar se é WhatsApp
                    if self.detectar_whatsapp(json_data):
                        print(f"   🎯 MENSAGEM DO WHATSAPP DETECTADA!")
                        self.processar_mensagem_whatsapp(json_data)

                except json.JSONDecodeError:
                    print(f"   📝 Texto simples: {content}")
            else:
                print(f"   ❌ String vazia após strip()")

        # Se for dict/objeto
        elif isinstance(content, dict):
            print(f"   📊 Objeto/Dict encontrado:")
            print(json.dumps(content, indent=6, ensure_ascii=False))

            if self.detectar_whatsapp(content):
                print(f"   🎯 MENSAGEM DO WHATSAPP DETECTADA!")
                self.processar_mensagem_whatsapp(content)

        else:
            print(f"   🔍 Tipo não reconhecido: {type(content)}")
            print(f"   📄 Valor: {repr(content)}")

    def detectar_whatsapp(self, data):
        """Detecta se é mensagem do WhatsApp"""
        if not isinstance(data, dict):
            return False

        # Campos típicos de webhook do WhatsApp/W-API
        campos_whatsapp = [
            'event', 'instanceId', 'connectedPhone', 'sender',
            'chat', 'msgContent', 'messageId', 'fromMe',
            'isGroup', 'moment', 'phone', 'message'
        ]

        encontrados = sum(1 for campo in campos_whatsapp if campo in data)
        return encontrados >= 2

    def processar_mensagem_whatsapp(self, data):
        """Processa mensagem específica do WhatsApp"""
        print(f"   📱 DETALHES DA MENSAGEM WHATSAPP:")

        campos_importantes = {
            'sender': 'Remetente',
            'chat': 'Chat',
            'msgContent': 'Conteúdo',
            'messageId': 'ID da Mensagem',
            'fromMe': 'De mim',
            'isGroup': 'É grupo',
            'moment': 'Momento'
        }

        for campo, nome in campos_importantes.items():
            if campo in data:
                print(f"      {nome}: {data[campo]}")

    def analisar_headers_e_extras(self, req):
        """Analisa headers e dados extras"""
        print(f"\n🔧 DADOS TÉCNICOS:")

        # Headers se existirem
        if 'headers' in req:
            print(f"   📡 Headers:")
            headers = req['headers']
            if isinstance(headers, dict):
                for key, value in headers.items():
                    print(f"      {key}: {value}")

        # URL e query parameters
        if 'url' in req:
            print(f"   🔗 URL: {req['url']}")

        if 'query' in req and req['query']:
            print(f"   ❓ Query params: {req['query']}")

    def monitorar_tempo_real_melhorado(self):
        """Monitoramento em tempo real mais eficiente"""
        print(f"\n🔄 MONITORAMENTO EM TEMPO REAL MELHORADO")
        print("=" * 50)
        print(f"🔗 Webhook URL: {self.webhook_url}")
        print(f"📡 API URL: {self.url_api}")
        print(f"⏱️ Intervalo de verificação: 2 segundos")
        print(f"💡 Pressione Ctrl+C para parar")
        print("=" * 50)

        contador_requisicoes = 0
        ultima_atividade = datetime.now()

        try:
            while True:
                print(f"\r🔍 Verificando... ({datetime.now().strftime('%H:%M:%S')})", end="", flush=True)

                requisicoes_novas = self.buscar_requisicoes_novas()

                if requisicoes_novas:
                    print()  # Nova linha após o status
                    ultima_atividade = datetime.now()

                    for req in requisicoes_novas:
                        contador_requisicoes += 1
                        self.analisar_requisicao_completa(req, contador_requisicoes)

                        # Separador entre requisições
                        print(f"\n{'=' * 20} FIM DA REQUISIÇÃO #{contador_requisicoes} {'=' * 20}")

                # Mostrar status a cada 30 segundos
                agora = datetime.now()
                if (agora - ultima_atividade).seconds > 30:
                    print(
                        f"\n⏰ Aguardando há {(agora - ultima_atividade).seconds}s... Total processadas: {contador_requisicoes}")
                    ultima_atividade = agora

                time.sleep(2)  # Verificar a cada 2 segundos

        except KeyboardInterrupt:
            print(f"\n\n👋 Monitoramento interrompido!")
            print(f"📊 Total de requisições processadas: {contador_requisicoes}")
            print(f"🕐 Sessão durou: {datetime.now().strftime('%H:%M:%S')}")

    def executar_debug_completo(self):
        """Executa sequência completa de debug"""
        print("🚀 INICIANDO DEBUG COMPLETO DO WEBHOOK")
        print("=" * 60)

        # 1. Testar conectividade
        if not self.testar_conectividade():
            print("❌ Falha na conectividade. Abortando...")
            return

        # 2. Análise inicial das requisições existentes
        print(f"\n📋 ANÁLISE INICIAL DAS REQUISIÇÕES EXISTENTES")
        print("=" * 40)

        requisicoes_existentes = self.buscar_requisicoes_novas()

        if requisicoes_existentes:
            print(f"✅ Encontradas {len(requisicoes_existentes)} requisições")
            for i, req in enumerate(requisicoes_existentes, 1):
                self.analisar_requisicao_completa(req, i)
        else:
            print("ℹ️ Nenhuma requisição encontrada ainda")

        # 3. Perguntar sobre monitoramento
        print(f"\n❓ DESEJA INICIAR MONITORAMENTO EM TEMPO REAL?")
        print("   • Digite 's' para SIM")
        print("   • Digite 'n' para NÃO")
        print("   • Qualquer outra tecla para sair")

        opcao = input("\nSua escolha: ").lower().strip()

        if opcao == 's':
            self.monitorar_tempo_real_melhorado()
        elif opcao == 'n':
            print("👍 Ok! Debug concluído.")
        else:
            print("👋 Saindo...")


def main():
    """Função principal melhorada"""
    print("🔍 WEBHOOK DEBUG MELHORADO v2.0")
    print("=" * 60)
    print("🎯 Análise completa e monitoramento em tempo real")
    print("🚀 Versão otimizada para detectar problemas")
    print("=" * 60)

    try:
        debug = WebhookDebugMelhorado(WEBHOOK_ID)
        debug.executar_debug_completo()

    except KeyboardInterrupt:
        print("\n👋 Programa interrompido pelo usuário!")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()

        print(f"\n💡 DICAS PARA RESOLVER:")
        print("   1. Verifique sua conexão com a internet")
        print("   2. Confirme se o webhook ID está correto")
        print("   3. Teste o webhook em um navegador")


if __name__ == '__main__':
    main()

# ===============================================
# 🔧 MELHORIAS IMPLEMENTADAS:
# ===============================================
#
# ✅ Monitoramento mais eficiente (apenas requisições novas)
# ✅ Melhor identificação de requisições únicas
# ✅ Análise mais detalhada do conteúdo
# ✅ Busca em campos alternativos quando conteúdo vazio
# ✅ Detecção melhorada de mensagens WhatsApp
# ✅ Tratamento de erros mais robusto
# ✅ Interface mais clara e informativa
# ✅ Redução do intervalo de verificação (2s)
# ✅ Status de progresso em tempo real
#
# 🚀 PRINCIPAIS CORREÇÕES:
# ===============================================
#
# 🔧 Sistema de IDs únicos mais confiável
# 🔧 Verificação de conectividade antes de monitorar
# 🔧 Análise de TODOS os campos da requisição
# 🔧 Melhor tratamento de timeouts e erros de rede
# 🔧 Interface mais responsiva
#
# ===============================================
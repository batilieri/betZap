🚀 INÍCIO RÁPIDO - WhatsApp Clone v2.0
⚡ Instalação Express (3 minutos)
🔥 Opção 1: Instalador Automático (Recomendado)
# 1. Clone o projeto
git clone <url-do-repositorio>
cd whatsapp-clone-v2

# 2. Execute o instalador
python install.py

# 3. Siga as instruções na tela
# ✅ Pronto! O instalador faz tudo automaticamente
🛠️ Opção 2: Instalação Manual
# 1. Criar ambiente virtual
python -m venv venv

# 2. Ativar ambiente
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar
python main.py
⚙️ Configuração W-API (1 minuto)
1. Obter Credenciais W-API
Você precisa de:

🌐 URL Base: https://api.w-api.com (ou sua instância)
🔑 Token: Token de acesso da sua conta
📱 Instance ID: ID da sua instância WhatsApp
2. Configurar no App
Abra o WhatsApp Clone
Clique em ⚙️ API → Configurar API
Preencha os campos:
URL Base da API: https://api.w-api.com
Token: seu_token_aqui
ID da Instância: 123456
Clique "Testar Conexão"
Se ✅, clique "OK"
💬 Primeiro Uso (30 segundos)
📥 Sincronizar Chats
Clique no botão 🔄 na barra lateral
Aguarde sincronização
Seus chats reais aparecem na lista
📤 Enviar Primeira Mensagem
Selecione um contato na lista
Digite uma mensagem no campo inferior
Pressione Enter ou clique "Enviar"
✅ Mensagem enviada via W-API!
🎯 Principais Funcionalidades
✅ O que FUNCIONA:
📱 Envio de mensagens reais via W-API
📥 Sincronização de chats do WhatsApp
👥 Lista de contatos atualizada
🔄 Status da API em tempo real
💾 Salvamento automático de conversas
🌙 Interface escura moderna
🚧 Em Desenvolvimento:
📸 Envio de mídias (imagens/vídeos)
👥 Grupos completos
🔔 Notificações push
🤖 Respostas automáticas
🆘 Resolução Rápida de Problemas
❌ "API: Não configurada"
Solução: Configure através do menu ⚙️ API → Configurar API

❌ "Erro HTTP 401"
Causa: Token inválido Solução: Verifique e atualize o token nas configurações

❌ "Chats não sincronizam"
Solução:

Verifique se a instância está conectada
Clique em 🔄 para forçar sincronização
Confirme permissões da API
❌ App não abre
Solução:

# Verificar dependências
pip install PyQt6 requests

# Ou reinstalar tudo
pip install -r requirements.txt
📋 Comandos Úteis
🔄 Executar Aplicativo
# Através do ambiente virtual
venv/Scripts/activate  # Windows
source venv/bin/activate  # Linux/Mac
python main.py

# Ou usar scripts
./run.sh  # Linux/Mac
run.bat   # Windows
🧹 Limpar Configurações
# Remover configurações salvas
rm -rf ~/.config/WhatsAppClone/  # Linux/Mac
# Windows: Del %APPDATA%\WhatsAppClone\
📦 Atualizar Dependências
pip install --upgrade -r requirements.txt
🔗 Links Importantes
📖 README Completo - Documentação detalhada
🐛 Issues - Reportar problemas
💡 Discussions - Ideias e dúvidas
📧 W-API Docs - Documentação da API
⭐ Dicas Pro
🚀 Performance
Mantenha no máximo 50 chats sincronizados
Feche chats antigos que não usa
Use o modo de economia de dados
🔒 Segurança
Nunca compartilhe seu token
Use URLs HTTPS sempre
Configure webhook em servidor seguro
🎨 Personalização
Ajuste fonte no código: QFont("Segoe UI", 14)
Modifique cores: background-color: #00D4AA;
Customize tema escuro/claro
🎉 Pronto para Usar!
Agora você tem um WhatsApp funcional integrado com a W-API!

📱 Envie mensagens reais
👥 Gerencie seus contatos
⚡ Interface moderna e rápida

💖 Gostou? Deixe uma ⭐ no repositório!

🤝 Problemas? Abra uma issue que ajudamos!
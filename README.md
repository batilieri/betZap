# 💬 WhatsApp Clone com PyQt6

Um clone moderno do WhatsApp Web desenvolvido em Python usando PyQt6, com interface escura e design responsivo.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6.1-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Características

- **Interface Moderna**: Design inspirado no WhatsApp Web com tema escuro
- **Layout Responsivo**: Interface adaptável que funciona em diferentes tamanhos de tela
- **Lista de Contatos**: Visualização de conversas com avatars, últimas mensagens e contadores de mensagens não lidas
- **Chat em Tempo Real**: Sistema de mensagens com bolhas de chat estilizadas
- **Status Online**: Indicadores de status dos contatos
- **Respostas Automáticas**: Sistema de simulação de respostas para demonstração
- **Scroll Automático**: Rolagem automática para novas mensagens
- **Temas Personalizáveis**: Interface com cores e estilos modernos

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes do Python)

### Passo a Passo

1. **Clone ou baixe o projeto**
   ```bash
   git clone <url-do-repositorio>
   cd whatsapp-clone
   ```

2. **Crie um ambiente virtual (recomendado)**
   ```bash
   python -m venv venv
   
   # No Windows
   venv\Scripts\activate
   
   # No Linux/Mac
   source venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute o aplicativo**
   ```bash
   python main.py
   ```

## 🎯 Como Usar

### Interface Principal

O aplicativo é dividido em duas seções principais:

1. **Painel Lateral (Lista de Chats)**
   - Mostra todos os contatos e conversas
   - Exibe última mensagem, horário e contador de mensagens não lidas
   - Clique em qualquer contato para abrir a conversa

2. **Painel de Chat**
   - Área de visualização das mensagens
   - Campo de entrada de texto na parte inferior
   - Botão "Enviar" ou pressione Enter para enviar mensagens

### Funcionalidades

#### ✅ Enviar Mensagens
- Digite sua mensagem no campo de texto inferior
- Pressione **Enter** ou clique no botão **"Enviar"**
- Suas mensagens aparecem em verde à direita
- Mensagens recebidas aparecem em cinza à esquerda

#### ✅ Trocar de Conversa
- Clique em qualquer contato na lista lateral
- A conversa será carregada no painel principal
- Mensagens não lidas serão marcadas como lidas automaticamente

#### ✅ Respostas Automáticas
- O sistema simula respostas automáticas após 2 segundos
- Respostas aleatórias são geradas para demonstração

### Atalhos de Teclado

- **Enter**: Enviar mensagem
- **Esc**: Limpar campo de texto (se implementado)

## 🛠️ Estrutura do Projeto

```
whatsapp-clone/
├── main.py              # Arquivo principal da aplicação
├── requirements.txt     # Dependências do projeto
├── README.md           # Documentação (este arquivo)
└── assets/             # Recursos (imagens, ícones) - opcional
```

## 🎨 Personalização

### Modificar Cores do Tema

No arquivo `main.py`, você pode alterar as cores editando os estilos CSS:

```python
# Cor principal (verde WhatsApp)
background-color: #00D4AA;

# Cor de fundo escura
background-color: #111B21;

# Cor das mensagens enviadas
background-color: #005C4B;

# Cor das mensagens recebidas
background-color: #202C33;
```

### Adicionar Novos Contatos

Modifique a função `load_sample_data()` para adicionar novos contatos:

```python
def load_sample_data(self):
    return {
        "Novo Contato": {
            "last_message": "Última mensagem",
            "time": "12:00",
            "unread": 0,
            "status": "online",
            "messages": []
        }
    }
```

## 🔧 Funcionalidades Avançadas

### Adicionar Persistência de Dados

Para salvar conversas entre sessões, você pode implementar:

```python
import json

def save_data(self):
    with open('chats.json', 'w', encoding='utf-8') as f:
        json.dump(self.chats_data, f, ensure_ascii=False, indent=2)

def load_data(self):
    try:
        with open('chats.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return self.load_sample_data()
```

### Adicionar Notificações

```python
from PyQt6.QtWidgets import QSystemTrayIcon
from PyQt6.QtGui import QIcon

def setup_notifications(self):
    self.tray_icon = QSystemTrayIcon(self)
    self.tray_icon.setIcon(QIcon("icon.png"))
    self.tray_icon.show()
```

## 🐛 Solução de Problemas

### Erro: "ModuleNotFoundError: No module named 'PyQt6'"

**Solução:**
```bash
pip install PyQt6
```

### Erro: "Qt platform plugin not found"

**Solução:**
```bash
pip uninstall PyQt6
pip install PyQt6 --force-reinstall
```

### Interface não aparece corretamente

**Verificações:**
1. Certifique-se de que está usando Python 3.8+
2. Verifique se todas as dependências estão instaladas
3. Teste em um ambiente virtual limpo

### Performance lenta

**Otimizações:**
1. Limite o número de mensagens carregadas simultaneamente
2. Implemente carregamento lazy para mensagens antigas
3. Otimize os estilos CSS complexos

## 📱 Compatibilidade

- **Sistemas Operacionais**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Resolução**: Mínima 800x600, Recomendada 1200x800+

## 🚀 Melhorias Futuras

- [ ] Sistema de autenticação
- [ ] Envio de arquivos e imagens
- [ ] Emojis e stickers
- [ ] Busca em mensagens
- [ ] Temas personalizáveis
- [ ] Notificações do sistema
- [ ] Backup automático de conversas
- [ ] Chamadas de voz/vídeo (simuladas)
- [ ] Grupos de conversa
- [ ] Criptografia de mensagens

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 👥 Créditos

- Design inspirado no WhatsApp Web
- Interface desenvolvida com PyQt6
- Ícones e elementos visuais baseados no design material

## 📞 Suporte

Se você encontrar problemas ou tiver dúvidas:

1. Verifique a seção de [Solução de Problemas](#-solução-de-problemas)
2. Abra uma issue no repositório
3. Consulte a documentação oficial do PyQt6

---

**Desenvolvido com ❤️ usando Python e PyQt6**
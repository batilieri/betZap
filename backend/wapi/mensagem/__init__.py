from .enviosMensagensDocs.enviarTexto import EnviaTexto
from .enviosMensagensDocs.enviarDocumento import EnviaDocumento
from .enviosMensagensDocs.enviarImagem import EnviaImagem
from .enviosMensagensDocs.enviarGif import EnviaGif
from .enviosMensagensDocs.enviarAudio import EnviaAudio
from .deletar.deletarMensagens import DeletaMensagem
from .editar.editarMensagens import EditarMensagem
from .reacao.enviarReacao import EnviarReacao
from .reacao.removerreacao import RemoverReacao

# Define o que será importado com "from whatsapp import *"
__all__ = [
    'EnviaTexto',
    'EnviaDocumento',
    'EnviaImagem',
    'EnviaGif',
    'EnviaAudio',
    'DeletaMensagem',
    'EditarMensagem',
    'EnviarReacao',
    'RemoverReacao'
]

# Variáveis do pacote
__version__ = '1.0.0'
__author__ = 'Elizeu Batiliere'

# Configurações padrão
DEFAULT_BASE_URL = "https://api.w-api.app/v1/"
DEFAULT_DELAY = 1

print(f"Pacote WhatsApp v{__version__} carregado!")
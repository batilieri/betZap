#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Execução da versão melhorada do chat
Com nomes corretos, barra de progresso e tempo real
"""

import sys
import os
from datetime import datetime


def check_requirements():
    """Verifica requisitos básicos"""
    print("🔍 Verificando requisitos...")

    # Verificar PyQt6
    try:
        import PyQt6
        print("✅ PyQt6 encontrado")
    except ImportError:
        print("❌ PyQt6 não encontrado")
        print("📦 Instale com: pip install PyQt6")
        return False

    # Verificar arquivos necessários
    required_files = [
        'database.py',
        'main_window.py',
        'ui/main_window_ui.py',
        'ui/chat_widget.py',
        'ui/__init__.py'
    ]

    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)

    if missing:
        print("❌ Arquivos em falta:")
        for file in missing:
            print(f"   - {file}")
        return False

    print("✅ Arquivos da interface encontrados")

    # Verificar banco
    db_path = 'backend/banco/whatsapp_webhook_realtime.db'
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path) / (1024 * 1024)
        print(f"✅ Banco encontrado: {db_size:.2f} MB")
    else:
        print(f"⚠️ Banco não encontrado: {db_path}")
        print("💡 Execute o webhook manager primeiro")

    return True


def print_improvements():
    """Mostra melhorias implementadas"""
    print("\n" + "=" * 60)
    print("💬 INTERFACE MELHORADA - WHATSAPP CHAT")
    print("=" * 60)

    print("\n🎯 MELHORIAS PRINCIPAIS:")
    print("   ✅ Nomes corretos da tabela 'senders'")
    print("   ✅ Barra de progresso elegante (sem popup)")
    print("   ✅ Atualização em tempo real (5s)")
    print("   ✅ Cache de nomes para performance")
    print("   ✅ Renderização estável sem sobreposição")
    print("   ✅ Detecção automática de novas mensagens")

    print("\n🎨 RECURSOS VISUAIS:")
    print("   • Barra de progresso no topo da janela")
    print("   • Progresso detalhado com porcentagens")
    print("   • Indicadores de carregamento suaves")
    print("   • Interface responsiva durante operações")

    print("\n⚡ PERFORMANCE:")
    print("   • Cache inteligente de nomes de contatos")
    print("   • Atualizações silenciosas em segundo plano")
    print("   • Verificação eficiente de novas mensagens")
    print("   • Renderização otimizada (max 50 mensagens)")

    print("\n⌨️ ATALHOS NOVOS:")
    print("   • Ctrl+D: Informações de debug")
    print("   • Ctrl+Shift+R: Atualizar cache de nomes")

    print("\n🔄 TEMPO REAL:")
    print("   • Verifica novas mensagens a cada 5 segundos")
    print("   • Atualiza interface automaticamente")
    print("   • Sem interrupção da experiência do usuário")

    print("=" * 60)


def main():
    """Função principal"""
    print_improvements()

    print(f"\n⏰ Iniciando às {datetime.now().strftime('%H:%M:%S')}")

    # Verificar requisitos
    if not check_requirements():
        print("\n❌ Requisitos não atendidos")
        return False

    print("\n🚀 Executando interface melhorada...")

    try:
        # Importar e executar
        from main_window import main as run_improved
        run_improved()

    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("\n💡 Certifique-se de que todos os arquivos estão presentes:")
        print("   - databas.py")
        print("   - main_window.py")
        print("   - ui/main_window_ui.py")
        print("   - ui/chat_widget.py")
        return False

    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == '__main__':
    try:
        success = main()
        if not success:
            input("\nPressione Enter para sair...")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Execução cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        input("\nPressione Enter para sair...")
        sys.exit(1)
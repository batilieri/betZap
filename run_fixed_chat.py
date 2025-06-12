#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Execução da versão CORRIGIDA do chat
SEM recarregamento total da interface ao carregar mensagens
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
        print("\n💡 Certifique-se de que os arquivos corrigidos estão no diretório")
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
    print("\n" + "=" * 70)
    print("💬 INTERFACE CORRIGIDA - WHATSAPP CHAT - SEM RECARREGAMENTO")
    print("=" * 70)

    print("\n🎯 PROBLEMA RESOLVIDO:")
    print("   ❌ ANTES: Interface recarregava totalmente a cada mensagem")
    print("   ✅ AGORA: Carregamento incremental sem recarregamento")

    print("\n🔧 CORREÇÕES IMPLEMENTADAS:")
    print("   ✅ Carregamento inicial de mensagens (apenas uma vez)")
    print("   ✅ Monitoramento incremental de novas mensagens")
    print("   ✅ Cache inteligente de mensagens por chat")
    print("   ✅ Interface mantém estado sem 'piscar'")
    print("   ✅ Separadores de data dinâmicos")
    print("   ✅ Animações suaves apenas para novas mensagens")

    print("\n⚡ PERFORMANCE OTIMIZADA:")
    print("   • Carregamento inicial: ~30 mensagens por chat")
    print("   • Verificação de novas: a cada 3 segundos")
    print("   • Cache de mensagens carregadas por chat")
    print("   • Sem reprocessamento de mensagens antigas")
    print("   • Interface sempre responsiva")

    print("\n🎨 EXPERIÊNCIA DO USUÁRIO:")
    print("   • Sem recarregamentos visuais")
    print("   • Mensagens novas aparecem suavemente")
    print("   • Scroll automático apenas para novas mensagens")
    print("   • Separadores de data inteligentes")
    print("   • Estado da interface preservado")

    print("\n🔄 SISTEMA DE ATUALIZAÇÕES:")
    print("   • Inicial: get_chat_messages_initial() - uma vez")
    print("   • Incremental: get_new_messages_incremental() - contínuo")
    print("   • Cache: _loaded_messages_cache por chat")
    print("   • Timestamp: _last_message_timestamps por chat")

    print("\n📱 THREADS OTIMIZADAS:")
    print("   1. OptimizedDatabaseWorker - Carregamento inicial")
    print("   2. IncrementalUpdater - Monitoramento (3s)")
    print("   3. MessageSender - Envio de mensagens")

    print("\n⌨️ ATALHOS:")
    print("   • Ctrl+D: Debug info + estatísticas de cache")
    print("   • Refresh: Força verificação de novas mensagens")

    print("=" * 70)


def backup_original_files():
    """Faz backup dos arquivos originais"""
    files_to_backup = [
        ('database.py', 'database_original.py'),
        ('main_window.py', 'main_window_original.py')
    ]

    backups_made = []
    for original, backup in files_to_backup:
        if os.path.exists(original) and not os.path.exists(backup):
            try:
                import shutil
                shutil.copy2(original, backup)
                backups_made.append(f"{original} → {backup}")
                print(f"📋 Backup criado: {backup}")
            except Exception as e:
                print(f"⚠️ Erro ao criar backup de {original}: {e}")

    if backups_made:
        print(f"✅ {len(backups_made)} backups criados")
    else:
        print("ℹ️ Backups já existem ou arquivos originais não encontrados")


def show_usage_instructions():
    """Mostra instruções de uso"""
    print("\n📖 INSTRUÇÕES DE USO:")
    print("\n1️⃣ PRIMEIRO USO:")
    print("   • Execute este script: python run_optimized_chat.py")
    print("   • Selecione um contato da lista")
    print("   • Aguarde carregamento inicial (30 mensagens)")
    print("   • Interface ficará ativa para monitoramento")

    print("\n2️⃣ FUNCIONAMENTO:")
    print("   • Mensagens antigas: carregadas uma vez")
    print("   • Mensagens novas: aparecem automaticamente")
    print("   • Sem recarregamento da interface")
    print("   • Cache mantido por chat")

    print("\n3️⃣ TESTE DA CORREÇÃO:")
    print("   • Abra o chat de um contato")
    print("   • Aguarde algumas verificações (3s cada)")
    print("   • Simule recebimento de mensagem")
    print("   • Verifique que interface NÃO recarrega")

    print("\n4️⃣ DEBUG:")
    print("   • Pressione Ctrl+D para ver estatísticas")
    print("   • Verifique cache de mensagens")
    print("   • Monitore logs no console")

    print("\n5️⃣ PERFORMANCE:")
    print("   • Cache por chat preservado")
    print("   • Apenas novas mensagens processadas")
    print("   • Interface sempre responsiva")


def main():
    """Função principal"""
    print_improvements()

    print(f"\n⏰ Iniciando às {datetime.now().strftime('%H:%M:%S')}")

    # Verificar requisitos
    if not check_requirements():
        print("\n❌ Requisitos não atendidos")
        input("\nPressione Enter para sair...")
        return False

    # Fazer backup dos arquivos originais
    print("\n🔄 Verificando backups...")
    backup_original_files()

    print("\n🚀 Executando interface CORRIGIDA...")

    try:
        # Importar e executar versão corrigida
        from main_window import main as run_optimized

        print("\n✅ Interface corrigida carregada")
        print("🎯 FOCO: Sem recarregamento total da interface")
        print("⚡ Monitoramento incremental ativo")

        show_usage_instructions()

        print(f"\n🔥 EXECUTANDO VERSÃO CORRIGIDA...")
        run_optimized()

    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("\n💡 Certifique-se de que os arquivos corrigidos estão presentes:")
        print("   - database_optimized.py")
        print("   - main_window_fixed.py")
        print("   - ui/main_window_ui.py")
        print("   - ui/chat_widget.py")
        return False

    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def show_comparison():
    """Mostra comparação entre versões"""
    print("\n📊 COMPARAÇÃO DE VERSÕES:")
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│                    ANTES vs DEPOIS                         │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│ PROBLEMA:           │ SOLUÇÃO:                              │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│ ❌ Interface pisca   │ ✅ Interface estável                 │")
    print("│ ❌ Recarrega tudo    │ ✅ Carregamento incremental          │")
    print("│ ❌ Lento e pesado    │ ✅ Rápido e eficiente               │")
    print("│ ❌ Perde posição     │ ✅ Mantém estado                     │")
    print("│ ❌ UX ruim           │ ✅ UX suave                          │")
    print("└─────────────────────────────────────────────────────────────┘")

    print("\n🔧 ARQUIVOS MODIFICADOS:")
    print("   📁 database.py → database_optimized.py")
    print("      • Cache de mensagens por chat")
    print("      • Métodos incrementais")
    print("      • Sem recarregamento total")

    print("\n   📁 main_window.py → main_window_fixed.py")
    print("      • IncrementalUpdater thread")
    print("      • Carregamento inicial único")
    print("      • Adição de mensagens únicas")

    print("\n🎯 RESULTADO:")
    print("   ✅ Interface NÃO recarrega ao receber mensagens")
    print("   ✅ Performance muito melhor")
    print("   ✅ UX profissional e suave")


if __name__ == '__main__':
    try:
        print("🎨 WHATSAPP CHAT INTERFACE - VERSÃO CORRIGIDA")
        print("🎯 Objetivo: Eliminar recarregamento total da interface")

        show_comparison()

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
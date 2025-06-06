#!/usr/bin/env python3
"""
Utilitários e ferramentas para gerenciar o banco de dados
Scripts auxiliares para manutenção, backup e análise
"""

import os
import json
import sqlite3
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from database_manager import WhatsAppDatabaseManager


class DatabaseUtils:
    """Utilitários para gerenciar o banco de dados"""

    def __init__(self, db_path="whatsapp_webhook.db"):
        self.db_path = db_path
        self.db_manager = WhatsAppDatabaseManager(db_path)

    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        Cria backup do banco de dados

        Args:
            backup_path: Caminho do backup (opcional)

        Returns:
            str: Caminho do arquivo de backup criado
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_whatsapp_{timestamp}.db"

        try:
            shutil.copy2(self.db_path, backup_path)
            size_mb = round(os.path.getsize(backup_path) / 1024 / 1024, 2)
            print(f"✅ Backup criado: {backup_path} ({size_mb} MB)")
            return backup_path
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return ""

    def export_to_json(self,
                       output_file: str = "whatsapp_export.json",
                       days_back: Optional[int] = None,
                       contact_id: Optional[str] = None) -> bool:
        """
        Exporta mensagens para JSON

        Args:
            output_file: Arquivo de saída
            days_back: Últimos N dias (opcional)
            contact_id: ID do contato específico (opcional)

        Returns:
            bool: True se exportou com sucesso
        """
        try:
            # Buscar mensagens com filtros
            messages = self.db_manager.search_messages(
                contact_id=contact_id,
                days_back=days_back if days_back else 365,
                limit=10000
            )

            export_data = {
                'export_date': datetime.now().isoformat(),
                'total_messages': len(messages),
                'filters': {
                    'days_back': days_back,
                    'contact_id': contact_id
                },
                'messages': messages
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            size_mb = round(os.path.getsize(output_file) / 1024 / 1024, 2)
            print(f"✅ Exportado: {output_file} ({len(messages)} mensagens, {size_mb} MB)")
            return True

        except Exception as e:
            print(f"❌ Erro ao exportar: {e}")
            return False

    def export_to_csv(self,
                      output_file: str = "whatsapp_export.csv",
                      days_back: Optional[int] = None) -> bool:
        """
        Exporta estatísticas para CSV

        Args:
            output_file: Arquivo de saída
            days_back: Últimos N dias (opcional)

        Returns:
            bool: True se exportou com sucesso
        """
        try:
            # Conectar diretamente ao SQLite para query customizada
            conn = sqlite3.connect(self.db_path)

            # Query para dados das mensagens
            query = """
            SELECT 
                we.created_at,
                we.event_type,
                we.from_me,
                we.is_group,
                s.sender_id,
                s.push_name,
                c.chat_id,
                mc.message_type,
                mc.text_content,
                we.moment
            FROM webhook_events we
            LEFT JOIN senders s ON we.id = s.event_id
            LEFT JOIN chats c ON we.id = c.event_id
            LEFT JOIN message_contents mc ON we.id = mc.event_id
            ORDER BY we.created_at DESC
            """

            if days_back:
                cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
                query += f" WHERE we.created_at >= '{cutoff_date}'"

            # Exportar para CSV usando pandas
            df = pd.read_sql_query(query, conn)
            df.to_csv(output_file, index=False, encoding='utf-8')
            conn.close()

            size_mb = round(os.path.getsize(output_file) / 1024 / 1024, 2)
            print(f"✅ CSV exportado: {output_file} ({len(df)} linhas, {size_mb} MB)")
            return True

        except Exception as e:
            print(f"❌ Erro ao exportar CSV: {e}")
            return False

    def clean_old_data(self, days_to_keep: int = 90) -> int:
        """
        Remove dados antigos do banco

        Args:
            days_to_keep: Dias para manter

        Returns:
            int: Número de registros removidos
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            with self.db_manager.get_session() as session:
                # Buscar eventos antigos
                from models import WebhookEvent
                old_events = session.query(WebhookEvent).filter(
                    WebhookEvent.created_at < cutoff_date
                ).all()

                count = len(old_events)

                if count > 0:
                    # Confirmar remoção
                    response = input(f"⚠️  Remover {count} registros anteriores a {cutoff_date.date()}? (s/N): ")
                    if response.lower() == 's':
                        for event in old_events:
                            session.delete(event)
                        session.commit()
                        print(f"✅ Removidos {count} registros antigos")
                        return count
                    else:
                        print("❌ Operação cancelada")
                        return 0
                else:
                    print(f"✅ Nenhum registro antigo encontrado")
                    return 0

        except Exception as e:
            print(f"❌ Erro ao limpar dados: {e}")
            return 0

    def analyze_database(self) -> Dict:
        """Análise detalhada do banco de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Estatísticas gerais
            cursor.execute("SELECT COUNT(*) FROM webhook_events")
            total_events = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM webhook_events WHERE from_me = 1")
            sent_messages = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM webhook_events WHERE from_me = 0")
            received_messages = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM webhook_events WHERE is_group = 1")
            group_messages = cursor.fetchone()[0]

            # Top contatos
            cursor.execute("""
                SELECT s.push_name, s.sender_id, COUNT(*) as count
                FROM webhook_events we
                JOIN senders s ON we.id = s.event_id
                WHERE we.is_group = 0
                GROUP BY s.sender_id
                ORDER BY count DESC
                LIMIT 10
            """)
            top_contacts = cursor.fetchall()

            # Tipos de mensagem
            cursor.execute("""
                SELECT mc.message_type, COUNT(*) as count
                FROM message_contents mc
                GROUP BY mc.message_type
                ORDER BY count DESC
            """)
            message_types = cursor.fetchall()

            # Atividade por hora
            cursor.execute("""
                SELECT strftime('%H', created_at) as hour, COUNT(*) as count
                FROM webhook_events
                GROUP BY hour
                ORDER BY hour
            """)
            hourly_activity = cursor.fetchall()

            # Atividade por dia da semana
            cursor.execute("""
                SELECT 
                    CASE strftime('%w', created_at)
                        WHEN '0' THEN 'Domingo'
                        WHEN '1' THEN 'Segunda'
                        WHEN '2' THEN 'Terça'
                        WHEN '3' THEN 'Quarta'
                        WHEN '4' THEN 'Quinta'
                        WHEN '5' THEN 'Sexta'
                        WHEN '6' THEN 'Sábado'
                    END as day_name,
                    COUNT(*) as count
                FROM webhook_events
                GROUP BY strftime('%w', created_at)
                ORDER BY strftime('%w', created_at)
            """)
            weekly_activity = cursor.fetchall()

            conn.close()

            analysis = {
                'total_events': total_events,
                'sent_messages': sent_messages,
                'received_messages': received_messages,
                'group_messages': group_messages,
                'private_messages': total_events - group_messages,
                'top_contacts': [{'name': name, 'id': contact_id, 'count': count}
                                 for name, contact_id, count in top_contacts],
                'message_types': [{'type': msg_type, 'count': count}
                                  for msg_type, count in message_types],
                'hourly_activity': [{'hour': hour, 'count': count}
                                    for hour, count in hourly_activity],
                'weekly_activity': [{'day': day, 'count': count}
                                    for day, count in weekly_activity],
                'database_size_mb': round(os.path.getsize(self.db_path) / 1024 / 1024, 2)
            }

            return analysis

        except Exception as e:
            print(f"❌ Erro na análise: {e}")
            return {}

    def print_analysis_report(self):
        """Imprime relatório de análise formatado"""
        analysis = self.analyze_database()

        if not analysis:
            print("❌ Não foi possível gerar análise")
            return

        print("\n" + "=" * 60)
        print("📊 RELATÓRIO DE ANÁLISE DO BANCO DE DADOS")
        print("=" * 60)

        print(f"\n📈 ESTATÍSTICAS GERAIS:")
        print(f"• Total de eventos: {analysis['total_events']:,}")
        print(f"• Mensagens enviadas: {analysis['sent_messages']:,}")
        print(f"• Mensagens recebidas: {analysis['received_messages']:,}")
        print(f"• Mensagens em grupos: {analysis['group_messages']:,}")
        print(f"• Mensagens privadas: {analysis['private_messages']:,}")
        print(f"• Tamanho do banco: {analysis['database_size_mb']} MB")

        print(f"\n👥 TOP 10 CONTATOS:")
        for contact in analysis['top_contacts'][:10]:
            name = contact['name'] or 'Sem nome'
            print(f"• {name[:20]:<20} {contact['count']:>5} mensagens")

        print(f"\n📱 TIPOS DE MENSAGEM:")
        for msg_type in analysis['message_types']:
            print(f"• {msg_type['type']:<15} {msg_type['count']:>5} mensagens")

        print(f"\n🕐 ATIVIDADE POR HORA:")
        for activity in analysis['hourly_activity']:
            hour = activity['hour']
            count = activity['count']
            bar = "█" * min(50, count // max(1, analysis['total_events'] // 500))
            print(f"• {hour}h {count:>5} {bar}")

        print(f"\n📅 ATIVIDADE POR DIA DA SEMANA:")
        for activity in analysis['weekly_activity']:
            day = activity['day']
            count = activity['count']
            bar = "█" * min(30, count // max(1, analysis['total_events'] // 300))
            print(f"• {day:<8} {count:>5} {bar}")

        print("=" * 60)

    def optimize_database(self) -> bool:
        """Otimiza o banco de dados (VACUUM)"""
        try:
            print("🔧 Otimizando banco de dados...")
            old_size = os.path.getsize(self.db_path)

            conn = sqlite3.connect(self.db_path)
            conn.execute("VACUUM")
            conn.close()

            new_size = os.path.getsize(self.db_path)
            saved_mb = round((old_size - new_size) / 1024 / 1024, 2)

            print(f"✅ Banco otimizado! Economizou {saved_mb} MB")
            return True

        except Exception as e:
            print(f"❌ Erro ao otimizar: {e}")
            return False


def main():
    """Função principal para utilitários do banco"""
    import argparse

    parser = argparse.ArgumentParser(description='Utilitários do Banco de Dados WhatsApp')
    parser.add_argument('--db', '-d', type=str, default="whatsapp_webhook.db",
                        help='Arquivo do banco (padrão: whatsapp_webhook.db)')

    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')

    # Comando backup
    backup_parser = subparsers.add_parser('backup', help='Criar backup do banco')
    backup_parser.add_argument('--output', '-o', type=str, help='Arquivo de saída do backup')

    # Comando export-json
    json_parser = subparsers.add_parser('export-json', help='Exportar para JSON')
    json_parser.add_argument('--output', '-o', type=str, default='whatsapp_export.json',
                             help='Arquivo de saída')
    json_parser.add_argument('--days', type=int, help='Últimos N dias')
    json_parser.add_argument('--contact', type=str, help='ID do contato específico')

    # Comando export-csv
    csv_parser = subparsers.add_parser('export-csv', help='Exportar para CSV')
    csv_parser.add_argument('--output', '-o', type=str, default='whatsapp_export.csv',
                            help='Arquivo de saída')
    csv_parser.add_argument('--days', type=int, help='Últimos N dias')

    # Comando clean
    clean_parser = subparsers.add_parser('clean', help='Limpar dados antigos')
    clean_parser.add_argument('--keep-days', type=int, default=90,
                              help='Dias para manter (padrão: 90)')

    # Comando analyze
    subparsers.add_parser('analyze', help='Analisar banco de dados')

    # Comando optimize
    subparsers.add_parser('optimize', help='Otimizar banco de dados')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Verificar se arquivo existe
    if not os.path.exists(args.db):
        print(f"❌ Arquivo do banco não encontrado: {args.db}")
        return

    utils = DatabaseUtils(args.db)

    if args.command == 'backup':
        utils.backup_database(args.output)

    elif args.command == 'export-json':
        utils.export_to_json(
            output_file=args.output,
            days_back=args.days,
            contact_id=args.contact
        )

    elif args.command == 'export-csv':
        utils.export_to_csv(
            output_file=args.output,
            days_back=args.days
        )

    elif args.command == 'clean':
        utils.clean_old_data(args.keep_days)

    elif args.command == 'analyze':
        utils.print_analysis_report()

    elif args.command == 'optimize':
        utils.optimize_database()


if __name__ == '__main__':
    main()

# =============================================================================
# 🛠️ COMO USAR OS UTILITÁRIOS:
# =============================================================================
#
# 1. CRIAR BACKUP:
#    python database_utils.py backup
#    python database_utils.py backup --output backup_especial.db
#
# 2. EXPORTAR PARA JSON:
#    python database_utils.py export-json
#    python database_utils.py export-json --days 30 --contact 556999267344
#
# 3. EXPORTAR PARA CSV:
#    python database_utils.py export-csv
#    python database_utils.py export-csv --days 7 --output ultima_semana.csv
#
# 4. LIMPAR DADOS ANTIGOS:
#    python database_utils.py clean --keep-days 60
#
# 5. ANÁLISE COMPLETA:
#    python database_utils.py analyze
#
# 6. OTIMIZAR BANCO:
#    python database_utils.py optimize
#
# 7. USAR BANCO PERSONALIZADO:
#    python database_utils.py --db meu_banco.db analyze
#
# =============================================================================
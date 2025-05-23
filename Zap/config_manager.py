"""
Gerenciador de Configurações para WhatsApp Clone
Responsável por salvar e carregar configurações da aplicação
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from PyQt6.QtCore import QSettings


class ConfigManager:
    """Gerenciador centralizado de configurações"""

    def __init__(self, app_name: str = "WhatsAppClone"):
        self.app_name = app_name
        self.settings = QSettings("WhatsAppClone", "Application")
        self.config_dir = self._get_config_directory()
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_directory()

    def _get_config_directory(self) -> Path:
        """Obtém o diretório de configuração do sistema"""
        if os.name == 'nt':  # Windows
            config_path = Path(os.environ.get('APPDATA', '')) / self.app_name
        else:  # Linux/Mac
            config_path = Path.home() / f'.config/{self.app_name}'

        return config_path

    def _ensure_config_directory(self):
        """Garante que o diretório de configuração existe"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    # ===========================================
    # CONFIGURAÇÕES DA API
    # ===========================================

    def save_api_config(self, config: Dict[str, Any]):
        """Salva configurações da API"""
        api_config = {
            'base_url': config.get('base_url', ''),
            'token': config.get('token', ''),
            'instance_id': config.get('instance_id', ''),
            'webhook_url': config.get('webhook_url', ''),
            'webhook_enabled': config.get('webhook_enabled', False),
            'timeout': config.get('timeout', 15),
            'retry_attempts': config.get('retry_attempts', 3)
        }

        # Salvar via QSettings (mais seguro)
        for key, value in api_config.items():
            self.settings.setValue(f"api/{key}", value)

        # Também salvar em JSON para backup
        self._save_json_config('api', api_config)

    def load_api_config(self) -> Dict[str, Any]:
        """Carrega configurações da API"""
        config = {}

        # Tentar carregar do QSettings primeiro
        for key in ['base_url', 'token', 'instance_id', 'webhook_url', 'webhook_enabled', 'timeout', 'retry_attempts']:
            value = self.settings.value(f"api/{key}")
            if value is not None:
                # Converter tipos específicos
                if key == 'webhook_enabled':
                    config[key] = self.settings.value(f"api/{key}", False, type=bool)
                elif key in ['timeout', 'retry_attempts']:
                    config[key] = self.settings.value(f"api/{key}", 15 if key == 'timeout' else 3, type=int)
                else:
                    config[key] = str(value)

        # Se não encontrou no QSettings, tentar JSON
        if not config:
            config = self._load_json_config('api', {})

        return config

    def get_api_status(self) -> Dict[str, Any]:
        """Obtém status das configurações da API"""
        config = self.load_api_config()

        return {
            'configured': bool(config.get('base_url') and config.get('token') and config.get('instance_id')),
            'base_url_set': bool(config.get('base_url')),
            'token_set': bool(config.get('token')),
            'instance_id_set': bool(config.get('instance_id')),
            'webhook_configured': bool(config.get('webhook_url') and config.get('webhook_enabled'))
        }

    # ===========================================
    # CONFIGURAÇÕES DA INTERFACE
    # ===========================================

    def save_ui_config(self, config: Dict[str, Any]):
        """Salva configurações da interface"""
        ui_config = {
            'window_geometry': config.get('window_geometry', ''),
            'window_state': config.get('window_state', ''),
            'splitter_sizes': config.get('splitter_sizes', [400, 800]),
            'theme': config.get('theme', 'dark'),
            'font_size': config.get('font_size', 13),
            'auto_scroll': config.get('auto_scroll', True),
            'show_timestamps': config.get('show_timestamps', True),
            'notification_sound': config.get('notification_sound', True),
            'minimize_to_tray': config.get('minimize_to_tray', False)
        }

        for key, value in ui_config.items():
            self.settings.setValue(f"ui/{key}", value)

    def load_ui_config(self) -> Dict[str, Any]:
        """Carrega configurações da interface"""
        return {
            'window_geometry': self.settings.value("ui/window_geometry", ""),
            'window_state': self.settings.value("ui/window_state", ""),
            'splitter_sizes': self.settings.value("ui/splitter_sizes", [400, 800]),
            'theme': self.settings.value("ui/theme", "dark"),
            'font_size': self.settings.value("ui/font_size", 13, type=int),
            'auto_scroll': self.settings.value("ui/auto_scroll", True, type=bool),
            'show_timestamps': self.settings.value("ui/show_timestamps", True, type=bool),
            'notification_sound': self.settings.value("ui/notification_sound", True, type=bool),
            'minimize_to_tray': self.settings.value("ui/minimize_to_tray", False, type=bool)
        }

    # ===========================================
    # CONFIGURAÇÕES DE CHAT
    # ===========================================

    def save_chat_config(self, config: Dict[str, Any]):
        """Salva configurações de chat"""
        chat_config = {
            'max_messages_load': config.get('max_messages_load', 50),
            'auto_save_chats': config.get('auto_save_chats', True),
            'enable_typing_indicator': config.get('enable_typing_indicator', True),
            'auto_mark_read': config.get('auto_mark_read', True),
            'message_history_days': config.get('message_history_days', 30),
            'enable_emoji': config.get('enable_emoji', True),
            'compress_images': config.get('compress_images', True)
        }

        for key, value in chat_config.items():
            self.settings.setValue(f"chat/{key}", value)

    def load_chat_config(self) -> Dict[str, Any]:
        """Carrega configurações de chat"""
        return {
            'max_messages_load': self.settings.value("chat/max_messages_load", 50, type=int),
            'auto_save_chats': self.settings.value("chat/auto_save_chats", True, type=bool),
            'enable_typing_indicator': self.settings.value("chat/enable_typing_indicator", True, type=bool),
            'auto_mark_read': self.settings.value("chat/auto_mark_read", True, type=bool),
            'message_history_days': self.settings.value("chat/message_history_days", 30, type=int),
            'enable_emoji': self.settings.value("chat/enable_emoji", True, type=bool),
            'compress_images': self.settings.value("chat/compress_images", True, type=bool)
        }

    # ===========================================
    # DADOS DE CHAT (HISTÓRICO)
    # ===========================================

    def save_chat_data(self, chat_data: Dict[str, Any]):
        """Salva dados dos chats (histórico de mensagens)"""
        chat_file = self.config_dir / "chats.json"

        try:
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erro ao salvar chats: {e}")
            return False

    def load_chat_data(self) -> Dict[str, Any]:
        """Carrega dados dos chats salvos"""
        chat_file = self.config_dir / "chats.json"

        try:
            if chat_file.exists():
                with open(chat_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar chats: {e}")

        return {}

    def backup_chat_data(self) -> bool:
        """Cria backup dos dados de chat"""
        from datetime import datetime

        chat_file = self.config_dir / "chats.json"
        if not chat_file.exists():
            return False

        backup_dir = self.config_dir / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"chats_backup_{timestamp}.json"

        try:
            import shutil
            shutil.copy2(chat_file, backup_file)

            # Manter apenas os 5 backups mais recentes
            backups = sorted(backup_dir.glob("chats_backup_*.json"))
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    old_backup.unlink()

            return True
        except Exception as e:
            print(f"Erro ao criar backup: {e}")
            return False

    # ===========================================
    # CONFIGURAÇÕES AVANÇADAS
    # ===========================================

    def save_advanced_config(self, config: Dict[str, Any]):
        """Salva configurações avançadas"""
        advanced_config = {
            'debug_mode': config.get('debug_mode', False),
            'log_level': config.get('log_level', 'INFO'),
            'api_cache_enabled': config.get('api_cache_enabled', True),
            'api_cache_duration': config.get('api_cache_duration', 300),  # 5 minutos
            'auto_update_check': config.get('auto_update_check', True),
            'telemetry_enabled': config.get('telemetry_enabled', False),
            'experimental_features': config.get('experimental_features', False)
        }

        for key, value in advanced_config.items():
            self.settings.setValue(f"advanced/{key}", value)

    def load_advanced_config(self) -> Dict[str, Any]:
        """Carrega configurações avançadas"""
        return {
            'debug_mode': self.settings.value("advanced/debug_mode", False, type=bool),
            'log_level': self.settings.value("advanced/log_level", "INFO"),
            'api_cache_enabled': self.settings.value("advanced/api_cache_enabled", True, type=bool),
            'api_cache_duration': self.settings.value("advanced/api_cache_duration", 300, type=int),
            'auto_update_check': self.settings.value("advanced/auto_update_check", True, type=bool),
            'telemetry_enabled': self.settings.value("advanced/telemetry_enabled", False, type=bool),
            'experimental_features': self.settings.value("advanced/experimental_features", False, type=bool)
        }

    # ===========================================
    # MÉTODOS AUXILIARES
    # ===========================================

    def _save_json_config(self, section: str, config: Dict[str, Any]):
        """Salva configuração em arquivo JSON"""
        json_file = self.config_dir / f"{section}.json"

        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar {section} em JSON: {e}")

    def _load_json_config(self, section: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
        """Carrega configuração de arquivo JSON"""
        if default is None:
            default = {}

        json_file = self.config_dir / f"{section}.json"

        try:
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar {section} do JSON: {e}")

        return default

    def reset_all_settings(self):
        """Reseta todas as configurações para padrão"""
        # Limpar QSettings
        self.settings.clear()

        # Remover arquivos JSON
        for json_file in self.config_dir.glob("*.json"):
            try:
                json_file.unlink()
            except Exception as e:
                print(f"Erro ao remover {json_file}: {e}")

    def export_settings(self, export_file: Path) -> bool:
        """Exporta todas as configurações para um arquivo"""
        try:
            export_data = {
                'api': self.load_api_config(),
                'ui': self.load_ui_config(),
                'chat': self.load_chat_config(),
                'advanced': self.load_advanced_config(),
                'export_timestamp': str(datetime.now()),
                'app_version': '2.0'
            }

            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"Erro ao exportar configurações: {e}")
            return False

    def import_settings(self, import_file: Path) -> bool:
        """Importa configurações de um arquivo"""
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # Importar cada seção
            if 'api' in import_data:
                self.save_api_config(import_data['api'])

            if 'ui' in import_data:
                self.save_ui_config(import_data['ui'])

            if 'chat' in import_data:
                self.save_chat_config(import_data['chat'])

            if 'advanced' in import_data:
                self.save_advanced_config(import_data['advanced'])

            return True
        except Exception as e:
            print(f"Erro ao importar configurações: {e}")
            return False

    def get_config_info(self) -> Dict[str, Any]:
        """Obtém informações sobre as configurações"""
        return {
            'config_dir': str(self.config_dir),
            'config_files': [f.name for f in self.config_dir.glob("*.json")],
            'api_configured': self.get_api_status()['configured'],
            'total_chats': len(self.load_chat_data()),
            'settings_keys': len(self.settings.allKeys())
        }


# Exemplo de uso
if __name__ == "__main__":
    config = ConfigManager()

    # Salvar configurações de API
    api_config = {
        'base_url': 'https://api.w-api.com',
        'token': 'hov0ig4dm6Qadw7qmFdRHCuul1G15YUno',
        'instance_id': 'LITE-YLOCZC-ZGHBVR',
        'webhook_enabled': True
    }
    config.save_api_config(api_config)

    # Carregar configurações
    loaded_config = config.load_api_config()
    print("Configuração carregada:", loaded_config)

    # Verificar status
    status = config.get_api_status()
    print("Status da API:", status)

    # Informações do config
    info = config.get_config_info()
    print("Informações:", info)
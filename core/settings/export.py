"""配置导入导出模块"""
from core.i18n import _
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional
from core.infrastructure.logger import log

class SettingsExporter:
    """配置导入导出器"""

    @staticmethod
    def import_config(file_path: str, settings: Dict[str, Any]) -> bool:
        """从文件导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)
            settings.update(imported)
            log('SUCCESS', f'配置已从 {file_path} 导入')
            return True
        except (IOError, json.JSONDecodeError) as e:
            log('ERROR', f'导入配置失败: {e}')
            return False

    @staticmethod
    def export_config(file_path: str, settings: Dict[str, Any]) -> bool:
        """导出配置到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            log('SUCCESS', f'配置已导出到 {file_path}')
            return True
        except IOError as e:
            log('ERROR', f'导出配置失败: {e}')
            return False

    @staticmethod
    def check_and_auto_export(settings: Dict[str, Any]) -> None:
        """检查是否需要自动导出配置"""
        if not settings.get('auto_export_config', False):
            return
        export_interval = settings.get('export_interval', _('common.every_week'))
        try:
            last_export = settings.get('last_export_time', 0)
            current_time = time.time()
            intervals = {_('core.settings.export.key_002'): 86400, _('core.settings.export.key_001'): 604800, _('core.settings.export.key_003'): 2592000}
            threshold = intervals.get(export_interval, 604800)
            if current_time - last_export >= threshold:
                SettingsExporter._auto_export_config(settings)
        except Exception as e:
            log('ERROR', f'检查自动导出失败: {e}')

    @staticmethod
    def _auto_export_config(settings: Dict[str, Any]) -> None:
        """自动导出配置"""
        try:
            from core.infrastructure.path_resolver import get_settings_dir
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_file = os.path.join(get_settings_dir(), f'settings_auto_{timestamp}.json')
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            settings['last_export_time'] = time.time()
            log('SUCCESS', f'配置已自动导出到 {export_file}')
        except Exception as e:
            log('ERROR', f'自动导出配置失败: {e}')

    @staticmethod
    def generate_auto_export_path() -> str:
        """生成自动导出文件路径"""
        from core.infrastructure.path_resolver import get_settings_dir
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return os.path.join(get_settings_dir(), f'settings_auto_{timestamp}.json')
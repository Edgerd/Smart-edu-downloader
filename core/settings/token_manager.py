"""Token 管理模块"""
from core.i18n import _
from typing import Optional
from core.infrastructure.logger import log
from core.network.token_crypto import encrypt_token, decrypt_token

class TokenManager:
    """Token 管理器"""

    @staticmethod
    def encrypt(token: str) -> str:
        """加密 Access Token"""
        if not token:
            return ''
        try:
            return encrypt_token(token)
        except Exception as e:
            log('ERROR', f'Token 加密失败: {e}')
            return token

    @staticmethod
    def decrypt(encrypted_token: str) -> str:
        """解密 Access Token

        解密失败时记录日志并返回原文，便于排查「密文损坏 / 机器指纹变更导致
        Fernet 密钥不一致」等问题，而非静默把坏 token 当作有效 token 继续使用。
        """
        if not encrypted_token:
            return ''
        try:
            return decrypt_token(encrypted_token)
        except Exception as e:
            log('WARNING', f'Token 解密失败，将使用原文: {e}')
            return encrypted_token

    @staticmethod
    def load_token() -> str:
        """加载 Access Token（加密值）"""
        try:
            from core.config.settings_manager import get_settings_manager
            return get_settings_manager().get('access_token', '')
        except Exception as e:
            log('WARNING', f'加载 Access Token 失败: {e}')
            return ''

    @staticmethod
    def get_display_info(token: str) -> str:
        """获取 Token 显示信息"""
        decrypted = TokenManager.decrypt(token)
        if decrypted:
            return f"{_('core.settings.token_manager.fstr_001')}{len(decrypted)}"
        return _('core.settings.token_manager.auto_002')
"""Token 加密/解密模块。

提供基于 cryptography.fernet 的 Token 加密与解密功能，
当 cryptography 未安装时自动降级为 XOR + Base64 加密。

主要功能：
    - encrypt_token: 加密文本为 Fernet 格式（或 XOR 降级）
    - decrypt_token: 解密 Fernet 格式密文
    - migrate_old_token: 检测并迁移旧版 XOR 格式到 Fernet
    - encrypt_proxy_password / decrypt_proxy_password: 代理密码专用加解密
"""
from core.i18n import _
import base64
import hashlib
import platform
from typing import Tuple
try:
    from cryptography.fernet import Fernet
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
_XOR_KEY = b'SED_TOKEN_KEY_2024'

def _get_machine_seed() -> bytes:
    """获取机器标识种子。

    综合机器名、平台信息和 CPU 核心数生成稳定的机器标识，
    用于派生 Fernet 加密密钥。

    Returns:
        32 字节的机器标识哈希值。
    """
    machine_info = f'{platform.node()}|{platform.machine()}|{platform.system()}'
    return hashlib.sha256(machine_info.encode('utf-8')).digest()

def _get_fernet_key() -> bytes:
    """生成 Fernet 加密密钥。

    基于机器标识种子派生 32 字节密钥，并使用 Fernet 要求的
    URL-safe Base64 编码格式。

    Returns:
        Fernet 格式的密钥（44 字节 base64 编码）。
    """
    seed = _get_machine_seed()
    return base64.urlsafe_b64encode(seed)

def _encrypt_xor(text: str) -> str:
    """使用 XOR + Base64 加密文本（降级方案）。

    当 cryptography 库未安装时使用此降级加密方案。

    Args:
        text: 待加密的明文文本。

    Returns:
        Base64 编码的密文字符串，前缀为 ``xor:`` 以标识加密方式。
    """
    text_bytes = text.encode('utf-8')
    key_len = len(_XOR_KEY)
    encrypted = bytes((b ^ _XOR_KEY[i % key_len] for i, b in enumerate(text_bytes)))
    return 'xor:' + base64.b64encode(encrypted).decode('ascii')

def _decrypt_xor(encrypted: str) -> str:
    """解密 XOR + Base64 格式的密文。

    Args:
        encrypted: Base64 编码的密文字符串。可带 ``xor:`` 前缀或不带。

    Returns:
        解密后的明文文本。

    Raises:
        ValueError: 当密文格式无效或解密结果不可读时抛出。
    """
    data = encrypted
    if data.startswith('xor:'):
        data = data[4:]
    try:
        raw = base64.b64decode(data)
    except Exception as exc:
        raise ValueError(_('core.network.token_crypto.auto_007')) from exc
    key_len = len(_XOR_KEY)
    decrypted = bytes((b ^ _XOR_KEY[i % key_len] for i, b in enumerate(raw)))
    try:
        return decrypted.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError(_('core.network.token_crypto.auto_002')) from exc

def _is_old_xor_format(encrypted: str) -> bool:
    """检测密文是否为旧版 XOR + Base64 格式。

    旧格式特征：Base64 解码后进行 XOR 运算，结果为可打印文本。

    Args:
        encrypted: 待检测的密文字符串。

    Returns:
        如果判定为旧版 XOR 格式则返回 True。
    """
    try:
        data = encrypted
        if data.startswith('xor:'):
            data = data[4:]
        raw = base64.b64decode(data)
        key_len = len(_XOR_KEY)
        decrypted = bytes((b ^ _XOR_KEY[i % key_len] for i, b in enumerate(raw)))
        decoded_str = decrypted.decode('utf-8')
        return all((c.isprintable() or c in ('\n', '\r', '\t') for c in decoded_str))
    except Exception:
        return False

def encrypt_token(text: str) -> str:
    """加密 Token 文本。

    优先使用 Fernet 对称加密（需要 cryptography 库），
    若未安装 cryptography 则自动降级为 XOR + Base64 加密。

    Args:
        text: 待加密的明文 Token。

    Returns:
        加密后的密文字符串。
        Fernet 格式以 ``gAAAAA`` 开头，XOR 格式以 ``xor:`` 开头。

    Raises:
        TypeError: 当输入不是字符串类型时抛出。
    """
    if not isinstance(text, str):
        raise TypeError(_('core.network.token_crypto.auto_004'))
    if HAS_CRYPTOGRAPHY:
        key = _get_fernet_key()
        fernet = Fernet(key)
        return fernet.encrypt(text.encode('utf-8')).decode('ascii')
    else:
        return _encrypt_xor(text)

def decrypt_token(encrypted: str) -> str:
    """解密 Token 密文。

    自动识别密文格式并进行相应解密：
    - 旧版 ``xor:`` 前缀格式使用 XOR 解密
    - Fernet 格式使用 Fernet 解密

    Args:
        encrypted: 待解密的密文字符串。

    Returns:
        解密后的明文 Token。

    Raises:
        TypeError: 当输入不是字符串类型时抛出。
        ValueError: 当密文格式无效或解密失败时抛出。
    """
    if not isinstance(encrypted, str):
        raise TypeError(_('core.network.token_crypto.auto_005'))
    if encrypted.startswith('xor:') or _is_old_xor_format(encrypted):
        return _decrypt_xor(encrypted)
    if not HAS_CRYPTOGRAPHY:
        raise ValueError(_('core.network.token_crypto.auto_003'))
    try:
        key = _get_fernet_key()
        fernet = Fernet(key)
        return fernet.decrypt(encrypted.encode('ascii')).decode('utf-8')
    except Exception as exc:
        raise ValueError(_('core.network.token_crypto.auto_001')) from exc

def migrate_old_token(encrypted: str) -> Tuple[str, bool]:
    """迁移旧版 XOR 格式的 Token 到 Fernet 格式。

    检测输入密文是否为旧版 XOR + Base64 格式，
    如果是，则解密后重新使用 Fernet 加密。

    Args:
        encrypted: 待迁移的密文字符串。

    Returns:
        包含两个元素的元组：
        - 新格式的密文字符串（若无需迁移则返回原值）
        - 是否执行了迁移操作（True 表示已从 XOR 迁移到 Fernet）

    Raises:
        TypeError: 当输入不是字符串类型时抛出。
    """
    if not isinstance(encrypted, str):
        raise TypeError(_('core.network.token_crypto.auto_006'))
    if not _is_old_xor_format(encrypted):
        return (encrypted, False)
    try:
        plaintext = _decrypt_xor(encrypted)
    except ValueError:
        return (encrypted, False)
    if HAS_CRYPTOGRAPHY:
        new_encrypted = encrypt_token(plaintext)
        return (new_encrypted, True)
    else:
        if not encrypted.startswith('xor:'):
            return (_encrypt_xor(plaintext), True)
        return (encrypted, False)

def encrypt_proxy_password(text: str) -> str:
    """加密代理服务器密码。

    与 encrypt_token 使用相同的加密机制，
    语义上区分 Token 与代理密码的用途。

    Args:
        text: 待加密的代理密码明文。

    Returns:
        加密后的密文字符串。

    Raises:
        TypeError: 当输入不是字符串类型时抛出。
    """
    return encrypt_token(text)

def decrypt_proxy_password(encrypted: str) -> str:
    """解密代理服务器密码。

    与 decrypt_token 使用相同的解密机制，
    语义上区分 Token 与代理密码的用途。

    Args:
        encrypted: 待解密的代理密码密文。

    Returns:
        解密后的代理密码明文。

    Raises:
        TypeError: 当输入不是字符串类型时抛出。
        ValueError: 当密文格式无效或解密失败时抛出。
    """
    return decrypt_token(encrypted)
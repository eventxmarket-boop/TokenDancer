"""
Cryptography utilities for storing sensitive API keys.
Currently uses Fernet (symmetric AES) with SECRET_KEY as the master.
In production, use a dedicated KMS (e.g. AWS KMS) instead.
"""

import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


def _get_fernet() -> Fernet:
    """Create a Fernet instance derived from SECRET_KEY."""
    key_bytes = settings.SECRET_KEY.encode()
    # Derive a 32-byte key and base64 encode it for Fernet
    derived = hashlib.sha256(key_bytes).digest()
    b64_key = base64.urlsafe_b64encode(derived)
    return Fernet(b64_key)


def encrypt_api_key(plain_key: str) -> str:
    """Encrypt an API key. Returns base64-encoded ciphertext."""
    if not plain_key:
        return ""
    f = _get_fernet()
    return f.encrypt(plain_key.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    """Decrypt an API key ciphertext. Returns plaintext."""
    if not ciphertext:
        return ""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


def mask_api_key(key: str) -> str:
    """
    Mask an API key for display.
    e.g. sk-abc123...xyz9
    """
    if not key:
        return ""
    if len(key) <= 8:
        return key[:2] + "****"
    return key[:8] + "****" + key[-4:]

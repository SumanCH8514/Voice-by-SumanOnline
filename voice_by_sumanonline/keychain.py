from __future__ import annotations

import logging
import os
from typing import Optional, Tuple

from dotenv import load_dotenv
import keyring
import keyring.errors

load_dotenv()

log = logging.getLogger("voice_by_sumanonline.keychain")

SERVICE_NAME = "Voice by SumanOnline"
KEY_NAME = "groq_api_key"

def get_api_key() -> Optional[str]:
    try:
        key = keyring.get_password(SERVICE_NAME, KEY_NAME)
        if key:
            return key
    except keyring.errors.KeyringError as e:
        log.warning("Keyring unavailable: %s", e)

    env_key = os.environ.get("GROQ_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()
    return None

def set_api_key(key: Optional[str]) -> bool:
    if not key:
        try:
            keyring.delete_password(SERVICE_NAME, KEY_NAME)
        except keyring.errors.PasswordDeleteError:
            pass
        except keyring.errors.KeyringError as e:
            log.warning("Keyring delete failed: %s", e)
            return False
        return True
    try:
        keyring.set_password(SERVICE_NAME, KEY_NAME, key)
        return True
    except keyring.errors.KeyringError as e:
        log.warning("Keyring set failed: %s", e)
        return False

def test_connection(api_key: str) -> Tuple[bool, str]:
    if not api_key:
        return False, "No API key provided."
    try:
        import httpx
    except ImportError:
        return False, "httpx not installed."
    try:
        r = httpx.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=4.0,
        )
        if r.status_code == 200:
            return True, "Connection successful."
        if r.status_code == 401:
            return False, "Invalid API key (401 Unauthorized)."
        return False, f"Groq API returned HTTP {r.status_code}: {r.text[:120]}"
    except httpx.ConnectError:
        return False, "Could not reach api.groq.com. Check network connectivity."
    except httpx.TimeoutException:
        return False, "Connection timed out after 4 seconds."
    except Exception as e:
        return False, f"Connection test failed: {e}"

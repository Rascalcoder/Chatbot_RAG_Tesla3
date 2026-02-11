"""
Hugging Face token loading helpers.
Supports .env and HUGGINGFACE_HUB_TOKEN.env without hardcoding secrets.
"""

import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def configure_hf_hub_defaults() -> None:
    """
    Configure safe defaults for Hugging Face downloads, especially on Windows/corporate networks.

    Notes:
    - We do NOT hardcode any secrets.
    - All settings are overrideable via environment variables.
    """
    # Reduce noisy Windows symlink warnings (does not change behavior)
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

    # Some corporate networks/timeouts struggle with Xet/CAS bridge; allow disabling it.
    # You can override by setting HF_HUB_DISABLE_XET=0 (or unsetting it).
    if os.name == "nt":
        os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

    # Be more tolerant to slow connections (seconds)
    os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "30")
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "600")


def _load_env_files() -> None:
    load_dotenv()
    token_env_path = os.getenv("HUGGINGFACE_TOKEN_FILE", "HUGGINGFACE_HUB_TOKEN.env")
    if token_env_path and os.path.exists(token_env_path):
        load_dotenv(token_env_path)


def _try_read_token_file_manually(token_env_path: str) -> str | None:
    """
    Fallback parser for token files that are NOT in dotenv KEY=VALUE format.
    Supports:
      - KEY=VALUE (single line)
      - Two-line format:
          HUGGINGFACE_HUB_TOKEN
          hf_....
    """
    try:
        # Try a few common encodings (handles UTF-8 BOM and some Windows editors)
        for enc in ("utf-8-sig", "utf-8", "utf-16"):
            try:
                with open(token_env_path, "r", encoding=enc) as f:
                    raw = f.read()
                break
            except UnicodeError:
                raw = ""
                continue
        if not raw:
            return None

        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if not lines:
            return None

        # Standard dotenv line(s)
        for ln in lines:
            if "=" in ln:
                k, v = ln.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k in ("HUGGINGFACE_HUB_TOKEN", "HF_TOKEN", "HUGGINGFACE_TOKEN") and v:
                    return v

        # Two-line format
        if len(lines) >= 2 and lines[0] in ("HUGGINGFACE_HUB_TOKEN", "HF_TOKEN", "HUGGINGFACE_TOKEN"):
            v = lines[1].strip().strip('"').strip("'")
            return v or None

        return None
    except Exception:
        return None


def get_hf_token() -> str | None:
    configure_hf_hub_defaults()
    _load_env_files()
    token_env_path = os.getenv("HUGGINGFACE_TOKEN_FILE", "HUGGINGFACE_HUB_TOKEN.env")
    token = (
        os.getenv("HUGGINGFACE_HUB_TOKEN")
        or os.getenv("HF_TOKEN")
        or os.getenv("HUGGINGFACE_TOKEN")
    )
    if not token and token_env_path and os.path.exists(token_env_path):
        token = _try_read_token_file_manually(token_env_path)
    # If still no token, check HuggingFace CLI cache (huggingface-cli login stores token there)
    if not token:
        try:
            hf_home = os.getenv("HF_HOME") or os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
            token_cache_path = os.path.join(hf_home, "token")
            if os.path.exists(token_cache_path):
                with open(token_cache_path, "r", encoding="utf-8") as f:
                    raw = f.read().strip()
                # Token file may contain just the token or JSON-like content; try to extract hf_...
                if raw:
                    # If the file contains the token directly, use it
                    if raw.startswith("hf_"):
                        token = raw
                    else:
                        # Try to find substring that looks like a token
                        import re

                        m = re.search(r"(hf_[A-Za-z0-9_-]{10,})", raw)
                        if m:
                            token = m.group(1)
        except Exception:
            # Non-fatal: ignore cache read errors
            token = token or None
    if token:
        token = token.strip().strip('"').strip("'")
    return token or None


def ensure_hf_token_env(silent: bool = False) -> str | None:
    """
    Ensure HF token is in environment.
    
    Args:
        silent: If True, suppress warning when token is not found (for public models)
    
    Returns:
        Token string or None
    """
    token = get_hf_token()
    if token and not os.getenv("HUGGINGFACE_HUB_TOKEN"):
        os.environ["HUGGINGFACE_HUB_TOKEN"] = token
    if not token and not silent:
        logger.warning("HF token not found in environment or token file. This is only needed for gated/private models.")
    return token


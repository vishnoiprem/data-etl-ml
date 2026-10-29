import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()


def get_apikey() -> str:
    """Read OPENAI_API_KEY from the environment (.env) or apikeys.yml."""
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key

    key_file = Path(__file__).with_name("apikeys.yml")
    if not key_file.exists():
        raise FileNotFoundError(
            "Missing apikeys.yml. Copy apikeys.example.yml to apikeys.yml "
            "and add your key, or set OPENAI_API_KEY in .env."
        )

    config = yaml.safe_load(key_file.read_text(encoding="utf-8")) or {}
    key = config.get("OPENAI_API_KEY") or config.get("openai_api_key")
    if not key or str(key).startswith("replace-"):
        raise ValueError("OPENAI_API_KEY is missing or still contains the placeholder.")
    return str(key)


if __name__ == "__main__":
    # Never print the secret itself.
    key = get_apikey()
    print(f"OpenAI API key loaded successfully (length={len(key)}).")

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    openai_api_key: str
    openai_vision_model: str = "gpt-4o"
    openai_timeout_seconds: float = 60.0
    openai_max_retries: int = 2
    max_image_bytes: int = 10 * 1024 * 1024

    @classmethod
    def from_env(cls):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("Falta OPENAI_API_KEY en las variables de entorno.")

        return cls(openai_api_key=api_key)
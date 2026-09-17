import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    # Variables obligatorias que vienen del .env
    openai_api_key: str
    langfuse_public_key: str
    langfuse_secret_key: str

    # Configuración con valores por defecto
    langfuse_host: str = "https://cloud.langfuse.com"
    openai_vision_model: str = "gpt-4o"
    openai_timeout_seconds: float = 60.0
    openai_max_retries: int = 2
    max_image_bytes: int = 10 * 1024 * 1024

    @classmethod
    def from_env(cls):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        langfuse_host = os.getenv(
            "LANGFUSE_HOST",
            "https://cloud.langfuse.com",
        )

        if not openai_api_key:
            raise ValueError(
                "Falta OPENAI_API_KEY en las variables de entorno."
            )

        if not langfuse_public_key:
            raise ValueError(
                "Falta LANGFUSE_PUBLIC_KEY en las variables de entorno."
            )

        if not langfuse_secret_key:
            raise ValueError(
                "Falta LANGFUSE_SECRET_KEY en las variables de entorno."
            )

        return cls(
            openai_api_key=openai_api_key,
            langfuse_public_key=langfuse_public_key,
            langfuse_secret_key=langfuse_secret_key,
            langfuse_host=langfuse_host,
        )
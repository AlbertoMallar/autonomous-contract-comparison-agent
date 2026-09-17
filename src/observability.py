from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from src.config import Settings
from src.errors import ObservabilityError



class LangfuseObservability:

    def __init__(self, settings: Settings) -> None:
        try:
            self.client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                base_url=settings.langfuse_host,
            )

        except Exception as exc:
            raise ObservabilityError(
                f"No se pudo inicializar Langfuse: {exc}"
            ) from exc

    def callback_handler(self):
        return CallbackHandler(
        public_key=self.public_key
    )

    def callback_handler(self):
        return CallbackHandler()

    def flush(self) -> None:
        try:
            self.client.flush()
        except Exception as exc:
            raise ObservabilityError(
                f"No se pudo enviar la traza a Langfuse: {exc}"
            ) from exc
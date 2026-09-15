from langfuse import Langfuse

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

    def test_observation(self) -> None:
        try:
            with self.client.start_as_current_observation(
                name="langfuse-test",
                as_type="span",
                input={"message": "Prueba de conexión"},
            ) as observation:

                observation.update(
                    output={"status": "ok"}
                )

            self.client.flush()

        except Exception as exc:
            raise ObservabilityError(
                f"No se pudo enviar la prueba a Langfuse: {exc}"
            ) from exc

if __name__ == "__main__":
    settings = Settings.from_env()

    observability = LangfuseObservability(settings)

    observability.test_observation()

    print("Observación enviada a Langfuse.")
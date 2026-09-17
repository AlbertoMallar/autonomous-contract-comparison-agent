import base64
import mimetypes
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)
from src.config import Settings
from src.errors import ImageValidationError, VisionParsingError

EXTENSIONES_PERMITIDAS = {".png", ".jpg", ".jpeg"}

VISION_PROMPT = """
Extraé fielmente todo el texto visible del documento legal de la imagen.

Reglas:
- Revisá el documento completo de arriba hacia abajo, incluyendo cualquier texto al final de la página.
- Conservá títulos, cláusulas, numeración y orden.
- Conservá exactamente nombres, fechas e importes.
- No omitas ninguna línea de texto visible.
- No resumas ni interpretes el contenido.
- No inventes información.
- Devolvé únicamente el texto extraído.
"""

def validate_image_path(
    image_path: str | Path,
    max_image_bytes: int,
) -> Path:

    ruta = Path(image_path).expanduser()

    if not ruta.exists():
        raise ImageValidationError(
            f"No existe la imagen: {ruta}"
        )

    if not ruta.is_file():
        raise ImageValidationError(
            f"La ruta no corresponde a un archivo: {ruta}"
        )

    if ruta.suffix.lower() not in EXTENSIONES_PERMITIDAS:
        raise ImageValidationError(
            f"Formato no permitido: {ruta.suffix}. Usá PNG, JPG o JPEG."
        )

    tamano = ruta.stat().st_size

    if tamano == 0:
        raise ImageValidationError(
            f"La imagen está vacía: {ruta}"
        )

    if tamano > max_image_bytes:
        limite_mb = max_image_bytes // (1024 * 1024)

        raise ImageValidationError(
            f"La imagen supera el límite de {limite_mb} MB: {ruta}"
        )

    try:
        with Image.open(ruta) as imagen:
            imagen.verify()

    except (UnidentifiedImageError, OSError) as exc:
        raise ImageValidationError(
            f"La imagen está corrupta o no puede decodificarse: {ruta}"
        ) from exc

    return ruta.resolve()


def encode_image_to_data_url(
    image_path: str | Path,
    max_image_bytes: int,
) -> str:

    # Valida la imagen antes de leerla.
    ruta = validate_image_path(
        image_path,
        max_image_bytes,
    )

    # Detecta el MIME type según el archivo.
    mime_type = mimetypes.guess_type(ruta.name)[0] or "image/png"

    # Lee y codifica la imagen en Base64.
    image_bytes = ruta.read_bytes()
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    # Construye la data URL correspondiente al formato real.
    return f"data:{mime_type};base64,{encoded_image}"


def parse_contract_image(
    image_path: str | Path,
    observation=None,
) -> str:

    settings = Settings.from_env()

    data_url = encode_image_to_data_url(
        image_path,
        settings.max_image_bytes,
    )

    client = OpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )

    try:
        response = client.responses.create(
            model=settings.openai_vision_model,
            instructions=VISION_PROMPT,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Transcribí el contenido de este documento.",
                        },
                        {
                            "type": "input_image",
                            "image_url": data_url,
                            "detail": "high",
                        },
                    ],
                }
            ],
        )

    except APITimeoutError as exc:
        raise VisionParsingError(
            "GPT-4o agotó el tiempo de espera al procesar la imagen."
        ) from exc

    except RateLimitError as exc:
        raise VisionParsingError(
            "OpenAI rechazó la llamada por límite de uso. Reintentá más tarde."
        ) from exc

    except APIConnectionError as exc:
        raise VisionParsingError(
            "No se pudo establecer conexión con OpenAI."
        ) from exc

    except APIStatusError as exc:
        raise VisionParsingError(
            f"OpenAI devolvió un error HTTP {exc.status_code}."
        ) from exc

    extracted_text = (response.output_text or "").strip()

    if not extracted_text:
        raise VisionParsingError(
            "GPT-4o no devolvió texto para la imagen."
        )

    usage = getattr(response, "usage", None)

    if observation is not None and usage is not None:
        observation.update(
            model=settings.openai_vision_model,
            usage_details={
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
            },
        )

    return extracted_text


import base64
from pathlib import Path
import os
from dotenv import load_dotenv
from openai import OpenAI



#cargamos la api key desde .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

def encode_image_to_data_url(image_path: Path) -> str:
    # Lee el contenido binario de la imagen.
    image_bytes = image_path.read_bytes()

    # Codifica esos bytes en Base64 y los convierte a texto
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    # Construye una data URL indicando que se trata de una imagen PNG en Base64.
    return f"data:image/png;base64,{encoded_image}"



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


def parse_contract_image(image_path: Path) -> str:

    #usamos la funcion anterior
    data_url = encode_image_to_data_url(image_path)

    #llamada al LLM
    response = client.responses.create(
        model="gpt-4o",
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

    return response.output_text


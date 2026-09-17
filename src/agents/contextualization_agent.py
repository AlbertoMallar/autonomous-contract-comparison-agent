from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

CONTEXTUALIZATION_PROMPT = """
Sos un analista legal senior especializado en estructura documental.

Recibís el texto completo de un contrato original y de su adenda.

Construí un mapa contextual y estructural comparativo que incluya:
- las secciones y cláusulas presentes en cada documento;
- el propósito general de cada sección o bloque;
- la correspondencia entre las secciones del contrato original y de la adenda.

Tu tarea es únicamente contextualizar la estructura documental.

No identifiques, extraigas ni describas los cambios introducidos por la adenda.
No compares valores, fechas, importes, plazos o condiciones.
No determines qué fue agregado, eliminado o modificado.
No inventes información.

Organizá la respuesta en:
1. Estructura del contrato original.
2. Estructura de la adenda.
3. Correspondencias entre ambos documentos.

- En la adenda, describí el propósito de cada sección con el mismo nivel de abstracción que en el contrato original, sin indicar la acción o el cambio que realiza.

Ejemplo:
"Cláusula 2 - Monto Mensual.
Propósito: regula las condiciones económicas del contrato.
Correspondencia: Cláusula 2 del contrato ↔ Cláusula 2 de la adenda."
Correcto: "Cláusula 3 - Vencimiento. Propósito: regula la vigencia temporal del contrato."
Incorrecto: "Propósito: extiende la fecha de vencimiento."

No hagas:
"El monto cambia de USD 1.000 a USD 1.500."
"""

model = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
)

#definimos la estructura del prompt
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CONTEXTUALIZATION_PROMPT),
        (
            "user",
            """
CONTRATO ORIGINAL:
{original_text}

ADENDA:
{amendment_text}
""",
        ),
    ]
)


chain = prompt | model


def contextualize_contracts(
    original_text: str,
    amendment_text: str,
    langfuse_handler=None,
) -> str:
    config = {
        "metadata": {
            "agent": "contextualization_agent",
            "purpose": "structural_mapping",
        }
    }

    if langfuse_handler is not None:
        config["callbacks"] = [langfuse_handler]

    response = chain.invoke(
        {
            "original_text": original_text,
            "amendment_text": amendment_text,
        },
        config=config,
    )

    return response.content


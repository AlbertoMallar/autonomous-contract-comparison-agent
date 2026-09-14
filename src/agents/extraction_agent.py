
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

#es nuestro modelo Pydantic que define la estructura obligatoria de salida.
from src.models import ContractChangeOutput
from pydantic import ValidationError

from src.errors import ContractOutputValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

EXTRACTION_PROMPT = """
Sos un auditor legal senior especializado en análisis de adendas contractuales.

Recibís:
- el texto completo del contrato original;
- el texto completo de la adenda;
- un mapa contextual que relaciona la estructura de ambos documentos.

Tu tarea es identificar los cambios introducidos por la adenda respecto del contrato original.

Analizá adiciones, eliminaciones y modificaciones concretas.
Usá el mapa contextual como guía para localizar las secciones relacionadas, pero verificá siempre los cambios contra los textos originales.

Devolvé:
- las secciones afectadas;
- los temas afectados;
- un resumen preciso de los cambios encontrados.

No inventes cambios que no estén respaldados por los documentos.
"""

model = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
)

#le exigimos al modelo devolver una respuesta compatible con nuestro modelo Pydantic.
structured_model = model.with_structured_output(ContractChangeOutput)

#organizamos las entradas
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", EXTRACTION_PROMPT),
        (
            "user",
            """
CONTRATO ORIGINAL:
{original_text}

ADENDA:
{amendment_text}

MAPA CONTEXTUAL:
{context_map}
""",
        ),
    ]
)

#el extractor devuelve una resp ajustada al contrato definido con Pydantic
chain = prompt | structured_model

def extract_changes(
    original_text: str,
    amendment_text: str,
    context_map: str,
) -> ContractChangeOutput:

    try:
        response = chain.invoke(
            {
                "original_text": original_text,
                "amendment_text": amendment_text,
                "context_map": context_map,
            }
        )

    except ValidationError as exc:
        raise ContractOutputValidationError(
            "La salida del extractor no cumple la estructura ContractChangeOutput."
        ) from exc

    return response



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
- el contrato original;
- la adenda;
- un mapa contextual de ambos documentos.

Identificá los cambios introducidos por la adenda respecto del contrato original:
adiciones, eliminaciones y modificaciones.

Usá el mapa contextual para localizar las secciones relacionadas, pero verificá
cada cambio contra los textos originales.

Devolvé:
- sections_changed: cláusulas o secciones afectadas;
- topics_touched: temas contractuales afectados;
- summary_of_the_change: resumen factual y preciso de los cambios.

Indicá claramente si cada cambio es una adición, eliminación o modificación.
No infieras consecuencias jurídicas, efectos o intenciones que no estén
explícitamente respaldados por los documentos.
No inventes información.
"""

model = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    max_tokens=2000,
    timeout=60,
    max_retries=2,
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
    langfuse_handler=None,
) -> ContractChangeOutput:

    config = {
        "metadata": {
            "agent": "extraction_agent",
            "purpose": "contract_change_extraction",
        }
    }

    if langfuse_handler is not None:
        config["callbacks"] = [langfuse_handler]

    try:
        response = chain.invoke(
            {
                "original_text": original_text,
                "amendment_text": amendment_text,
                "context_map": context_map,
            },
            config=config,
        )

    except ValidationError as exc:
        raise ContractOutputValidationError(
            "La salida del extractor no cumple la estructura ContractChangeOutput."
        ) from exc

    return response


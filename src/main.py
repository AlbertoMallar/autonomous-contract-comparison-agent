from pathlib import Path

from src.image_parser import parse_contract_image
from src.agents.contextualization_agent import contextualize_contracts
from src.agents.extraction_agent import extract_changes


ORIGINAL_PATH = Path(
    "data/test_contracts/caso_complejo/contrato_original.png"
)

AMENDMENT_PATH = Path(
    "data/test_contracts/caso_complejo/adenda.png"
)


def main():
    # 1. Extraer el texto de ambas imágenes.
    original_text = parse_contract_image(ORIGINAL_PATH)
    amendment_text = parse_contract_image(AMENDMENT_PATH)

    # 2. Construir el mapa estructural de ambos documentos.
    context_map = contextualize_contracts(
        original_text,
        amendment_text,
    )

    # 3. Identificar los cambios introducidos por la adenda.
    result = extract_changes(
        original_text,
        amendment_text,
        context_map,
    )

    # 4. Mostrar el resultado final validado por Pydantic.
    print("\n--- RESULTADO FINAL ---\n")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
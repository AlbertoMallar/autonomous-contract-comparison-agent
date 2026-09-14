import argparse
from pathlib import Path

from src.image_parser import parse_contract_image
from src.agents.contextualization_agent import contextualize_contracts
from src.agents.extraction_agent import extract_changes


TEST_CASES = {
    "simple": Path("data/test_contracts/caso_simple"),
    "complex": Path("data/test_contracts/caso_complejo"),
}


def main():
    #para ejecutar el programa desde terminal indicando qué documentos queremos analizar
    parser = argparse.ArgumentParser(
        description="Compara un contrato original con su adenda."
    )

    parser.add_argument(
        "original",
        nargs="?",
        help="Ruta de la imagen del contrato original.",
    )

    parser.add_argument(
        "amendment",
        nargs="?",
        help="Ruta de la imagen de la adenda.",
    )

    parser.add_argument(
        "--case",
        choices=["simple", "complex"],
        help="Ejecuta uno de los casos de prueba incluidos.",
    )

    #lee los argumentos que el usuario escribió en la terminal y los convierte en un objeto args que podemos consultar desde Python.
    args = parser.parse_args()

    if args.case:
        case_path = TEST_CASES[args.case]

        original_path = case_path / "contrato_original.png"
        amendment_path = case_path / "adenda.png"

    elif args.original and args.amendment:
        original_path = Path(args.original)
        amendment_path = Path(args.amendment)

    else:
        parser.error(
            "Indicá --case simple/complex o las rutas del contrato y la adenda."
        )

    #llamados al image_parser
    original_text = parse_contract_image(original_path)
    amendment_text = parse_contract_image(amendment_path)

    context_map = contextualize_contracts(
        original_text,
        amendment_text,
    )

    result = extract_changes(
        original_text,
        amendment_text,
        context_map,
    )

    print("\n--- RESULTADO FINAL ---\n")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
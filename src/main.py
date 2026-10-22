import argparse
from pathlib import Path

from src.config import Settings
from src.image_parser import parse_contract_image
from src.agents.contextualization_agent import contextualize_contracts
from src.agents.extraction_agent import extract_changes
from src.observability import LangfuseObservability
from src.errors import (
    ContractOutputValidationError,
    ImageValidationError,
    ObservabilityError,
    VisionParsingError,
)

TEST_CASES = {
    "simple": Path("data/test_contracts/caso_simple"),
    "complex": Path("data/test_contracts/caso_complejo"),
}


def main():
    
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

    settings = Settings.from_env()

    observability = LangfuseObservability(settings)
    langfuse_handler = observability.callback_handler()

    try:
        with observability.client.start_as_current_observation(
            name="contract-analysis",
            as_type="chain",
            input={
                "original_path": str(original_path),
                "amendment_path": str(amendment_path),
            },
        ) as observation:

            with observability.client.start_as_current_observation(
                name="parse_original_contract",
                as_type="generation",
                input={"image_path": str(original_path)},
                model=settings.openai_vision_model,
                metadata={
                    "stage": "vision_parsing",
                    "document": "original_contract",
                },

            ) as parse_original_observation:
                original_text = parse_contract_image(
                original_path,
                observation=parse_original_observation,
            )

                parse_original_observation.update(
                    output={"extracted_text": original_text}
                )

            with observability.client.start_as_current_observation(
                name="parse_amendment_contract",
                as_type="generation",
                input={"image_path": str(amendment_path)},
                model=settings.openai_vision_model,
                metadata={
                    "stage": "vision_parsing",
                    "document": "amendment_contract",
                },

            ) as parse_amendment_observation:
                amendment_text = parse_contract_image(
                amendment_path,
                observation=parse_amendment_observation,
            )

                parse_amendment_observation.update(
                    output={"extracted_text": amendment_text}
                )

            with observability.client.start_as_current_observation(
                name="contextualization_agent",
                as_type="span",
                input={
                    "original_text": original_text,
                    "amendment_text": amendment_text,
                },
            ) as contextualization_observation:
                context_map = contextualize_contracts(
                    original_text,
                    amendment_text,
                    langfuse_handler=langfuse_handler,
                )

                contextualization_observation.update(
                    output={"context_map": context_map}
                )


            with observability.client.start_as_current_observation(
                name="extraction_agent",
                as_type="span",
                input={
                    "original_text": original_text,
                    "amendment_text": amendment_text,
                    "context_map": context_map,
                },
            ) as extraction_observation:
                result = extract_changes(
                    original_text,
                    amendment_text,
                    context_map,
                    langfuse_handler=langfuse_handler,
                )

                extraction_observation.update(
                    output=result.model_dump(mode="json")
                )

            observation.update(output=result.model_dump(mode="json"))

            print("\n--- RESULTADO FINAL ---\n")
            print(result.model_dump_json(indent=2))
    finally:
        # La observación termina al salir del with, antes de vaciar la cola.
        observability.flush()


if __name__ == "__main__":
    try:
        main()
    except (
        ImageValidationError,
        VisionParsingError,
        ContractOutputValidationError,
        ObservabilityError,
        ValueError,
    ) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
class ImageValidationError(Exception):
    """Error al validar una imagen antes de enviarla al modelo."""


class VisionParsingError(Exception):
    """Error al procesar una imagen mediante el modelo multimodal."""


class ContractOutputValidationError(Exception):
    """Error cuando la salida del extractor no cumple el contrato Pydantic."""

class ObservabilityError(Exception):
    """Error al inicializar o enviar información a Langfuse."""
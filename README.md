# Autonomous Contract Comparison Agent

Proyecto Integrador del Módulo 4 de AI Engineering.

Sistema multiagente para comparar un contrato original con su adenda a partir de imágenes y producir una salida estructurada con las modificaciones, eliminaciones y adiciones contractuales detectadas.

El flujo es secuencial: transcribe ambos documentos con GPT-4o, construye un mapa contextual y extrae los cambios mediante dos agentes especializados con LangChain. Pydantic valida la estructura de la respuesta y Langfuse registra la ejecución por etapas.

## Arquitectura

```text
Contrato original (imagen) --> GPT-4o Vision --> texto original
Adenda (imagen) -----------> GPT-4o Vision --> texto adenda

                    texto original + texto adenda
                                  |
                                  v
                       Agente contextualizador
                                  |
                           mapa contextual
                                  |
                   mapa contextual + ambos textos
                                  |
                                  v
                          Agente extractor
                                  |
                                  v
                 ContractChangeOutput (JSON en consola)
```

### 1. Transcripción de imágenes

[`src/image_parser.py`](src/image_parser.py) recibe imágenes PNG, JPG o JPEG, valida el archivo, lo codifica en Base64 y lo envía a GPT-4o mediante la API Responses de OpenAI. El prompt solicita transcribir el documento conservando títulos, cláusulas, nombres, fechas e importes, sin resumir ni interpretar.

Se procesa una imagen por documento. El límite configurado por archivo es de 10 MiB (`10 * 1024 * 1024` bytes).

### 2. Contextualización

[`contextualize_contracts`](src/agents/contextualization_agent.py) recibe los dos textos y construye un mapa con sus secciones, propósitos y correspondencias. Su prompt delimita la tarea al análisis estructural, sin identificar cambios contractuales.

### 3. Extracción de cambios

[`extract_changes`](src/agents/extraction_agent.py) recibe el contrato original, la adenda y el mapa contextual. Identifica adiciones, eliminaciones y modificaciones, con la instrucción de verificar cada cambio contra los textos y evitar inferir consecuencias jurídicas no respaldadas por los documentos.

Ambos agentes utilizan `ChatOpenAI` con el modelo `gpt-4o` y `temperature=0`.

### 4. Salida estructurada

El extractor utiliza `with_structured_output(ContractChangeOutput)`. El modelo definido en [`src/models.py`](src/models.py) contiene:

| Campo | Tipo | Contenido |
| --- | --- | --- |
| `sections_changed` | `list[str]` | Cláusulas o secciones afectadas. |
| `topics_touched` | `list[str]` | Temas contractuales afectados. |
| `summary_of_the_change` | `str` | Resumen de los cambios detectados. |

El modelo rechaza campos adicionales y elimina espacios al inicio y al final de las cadenas. Pydantic valida la estructura y los tipos; no verifica la exactitud factual del análisis. Los prompts orientan el comportamiento de los agentes, pero tampoco garantizan que la transcripción o la comparación estén libres de errores.

## Instalación y configuración

### Requisitos

- Python 3.10 o superior y `pip`.
- Una clave de API de OpenAI con acceso a `gpt-4o`.
- Un proyecto de Langfuse con sus claves pública y secreta.
- Conexión a los servicios de OpenAI y Langfuse.

Ejecutar los siguientes comandos desde la raíz del proyecto.

### 1. Crear y activar un entorno virtual

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En macOS o Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar las dependencias

```bash
python -m pip install -r requirements.txt
```

Las versiones de las dependencias directas están fijadas en [`requirements.txt`](requirements.txt).

### 3. Configurar las credenciales

Copiar [`.env.example`](.env.example) a `.env` y completar los valores. Si ya existe un `.env` configurado, conservarlo.

En PowerShell:

```powershell
Copy-Item .env.example .env
```

En macOS o Linux:

```bash
cp .env.example .env
```

Contenido de `.env`:

```dotenv
OPENAI_API_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

`LANGFUSE_HOST` debe apuntar a la región o instancia del proyecto de Langfuse. Las tres claves son obligatorias en la configuración actual.

[`Settings`](src/config.py) carga estas variables y define los valores predeterminados del parser: modelo `gpt-4o`, timeout de 60 segundos, hasta 2 reintentos y límite de imagen de 10 MiB. El parser limita la salida de Vision a 6000 tokens; cada agente limita su salida a 2000 tokens por llamada. Los agentes configuran su modelo, timeout y reintentos en sus respectivos módulos. El archivo `.env` está excluido de Git mediante [`.gitignore`](.gitignore).

## Ejecución

Desde la raíz del proyecto, con el entorno virtual activo y las credenciales configuradas:

### Caso simple

```bash
python -m src.main --case simple
```

### Caso complejo

```bash
python -m src.main --case complex
```

### Documentos propios

Pasar primero la imagen del contrato original y luego la de la adenda:

```bash
python -m src.main "ruta/contrato.png" "ruta/adenda.png"
```

La interfaz actual acepta dos imágenes; no procesa PDF ni conjuntos de páginas directamente. Cada análisis realiza llamadas a la API de OpenAI.

### Resultado

El CLI imprime el encabezado `--- RESULTADO FINAL ---` y, a continuación, el resultado como JSON con indentación de dos espacios. Ejemplo de una salida real del caso simple, registrada el 17 de septiembre de 2026:

```json
{
  "sections_changed": [
    "Cláusula 2 - Monto Mensual",
    "Cláusula 3 - Vencimiento"
  ],
  "topics_touched": [
    "Condiciones económicas",
    "Vigencia temporal del contrato"
  ],
  "summary_of_the_change": "La adenda introduce las siguientes modificaciones al contrato original: \n\n1. **Cláusula 2 - Monto Mensual:** Se modifica el monto mensual que el cliente debe abonar, incrementándose de USD 1.000 a USD 1.500. \n\n2. **Cláusula 3 - Vencimiento:** Se extiende la fecha de vencimiento del contrato del 31 de diciembre de 2026 al 30 de junio de 2027."
}
```

La redacción puede variar entre ejecuciones. El programa muestra el resultado en consola; no lo guarda automáticamente en un archivo.

## Observabilidad con Langfuse

El pipeline está instrumentado con el SDK Python de Langfuse v4. Al iniciar el análisis se crea una observación raíz llamada `contract-analysis`. Las etapas principales de una ejecución completa son:

```text
contract-analysis                 [chain]
├── parse_original_contract       [generation]
├── parse_amendment_contract      [generation]
├── contextualization_agent      [span]
└── extraction_agent             [span]
```

Los agentes reciben un `CallbackHandler` de Langfuse, que añade observaciones de las operaciones internas de LangChain. Por eso, el árbol completo puede incluir más nodos que los mostrados en este esquema.

La instrumentación registra:

- Rutas de las imágenes en la entrada de la raíz y del parsing.
- Textos extraídos, mapa contextual y resultado final en las etapas correspondientes.
- Entradas y salidas de las cadenas de LangChain, incluidos sus prompts y respuestas.
- Duración de las observaciones y metadata de las etapas instrumentadas.
- Modelo y uso de tokens: registrados explícitamente en el parser cuando OpenAI devuelve `usage`, y mediante callbacks en las llamadas de LangChain.

Los costos se estiman en Langfuse a partir del modelo, los datos de uso y las tarifas que correspondan. El código no envía un costo monetario calculado manualmente; su disponibilidad depende de que Langfuse pueda asociar el modelo y las métricas de uso con su definición de precios. Ver [seguimiento de tokens y costos](https://langfuse.com/docs/observability/features/token-and-cost-tracking).

[`LangfuseObservability`](src/observability.py) reutiliza `Settings` para inicializar el cliente. El CLI llama a `observability.flush()` en un bloque `finally`, después de cerrar las observaciones, para vaciar los datos pendientes antes de salir, incluso si falla una etapa del análisis.

Para inspeccionar una ejecución, abrir el proyecto de Langfuse, buscar `contract-analysis` en **Tracing** y revisar sus observaciones. Las imágenes se envían a OpenAI para la transcripción; los textos de los documentos y los resultados del análisis se registran en Langfuse.

## Validaciones y manejo de errores

Las excepciones propias están definidas en [`src/errors.py`](src/errors.py):

| Área | Validaciones o errores contemplados |
| --- | --- |
| Configuración | Ausencia de las claves obligatorias de OpenAI o Langfuse. |
| Imágenes | Ruta inexistente, ruta que no es un archivo, extensión no admitida, archivo vacío, imagen corrupta o tamaño superior al límite. |
| Transcripción con OpenAI | Timeout, rate limit, error de conexión, error HTTP de la API y respuesta de texto vacía. |
| Extracción estructurada | `ValidationError` de Pydantic, convertido en `ContractOutputValidationError`. |
| Observabilidad | Excepciones que se propaguen durante la inicialización del cliente o la llamada a `flush()`, convertidas en `ObservabilityError`. |

El CLI muestra los errores que captura con el prefijo `Error:` y termina con código de salida `1`. El manejo específico de errores de OpenAI está implementado en el parser de imágenes; las llamadas de los agentes no tienen la misma traducción de excepciones.

## Casos de prueba

Los documentos se encuentran en [`data/test_contracts/`](data/test_contracts/README.md):

| Caso | Cambios esperados |
| --- | --- |
| `caso_simple` | Modificación del monto mensual y de la fecha de vencimiento. |
| `caso_complejo` | Ampliación del alcance territorial, eliminación de una restricción de uso y adición de una obligación de notificar incidentes de seguridad. |

Cada directorio contiene:

```text
contrato_original.png
adenda.png
expected.json
```

Los archivos `expected.json` sirven como referencia para una comparación manual. El CLI no los lee ni calcula automáticamente una puntuación o un resultado de aprobación. Para verificar un caso, ejecutar el comando correspondiente y contrastar las secciones, los temas y los cambios descritos con su referencia, sin exigir una coincidencia literal de redacción.

## Estructura del proyecto

```text
.
├── README.md
├── requirements.txt
├── .env.example
├── src/
│   ├── main.py
│   ├── config.py
│   ├── errors.py
│   ├── image_parser.py
│   ├── models.py
│   ├── observability.py
│   └── agents/
│       ├── contextualization_agent.py
│       └── extraction_agent.py
└── data/
    └── test_contracts/
        ├── README.md
        ├── caso_simple/
        └── caso_complejo/
```

## Decisiones de diseño

- **Separación de responsabilidades:** un agente construye el mapa estructural y otro identifica los cambios. El extractor recibe también ambos textos para contrastar la información con las fuentes.
- **LangChain:** compone los prompts y las llamadas a los modelos, incluida la salida estructurada del extractor.
- **Pydantic:** define un contrato de salida común para todos los casos, independiente de la redacción del modelo.
- **Langfuse:** permite inspeccionar entradas, salidas y tiempos por etapa, junto con las métricas de las llamadas al modelo.
- **Orquestación secuencial:** `main.py` coordina el flujo mediante llamadas directas. La aplicación no define un grafo con LangGraph: el flujo actual no incluye ramificaciones ni ciclos de agentes.

## Estado actual

El proyecto implementa transcripción multimodal, dos agentes especializados, salida estructurada, validación de imágenes, manejo de errores, ejecución por línea de comandos y observabilidad jerárquica con Langfuse. Incluye dos escenarios con resultados de referencia para revisión manual.

El alcance actual es la comparación de una imagen del contrato con una imagen de su adenda. La revisión de la exactitud de la transcripción y de los cambios detectados sigue siendo manual.

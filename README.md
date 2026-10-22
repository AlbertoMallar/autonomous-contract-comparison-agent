# Autonomous Contract Comparison Agent

A multimodal AI pipeline that compares an original contract with its amendment from document images. It transcribes both documents, maps their structure, and returns structured JSON describing the affected sections, topics, and contractual additions, removals, and modifications.

The command-line application combines **GPT-4o Vision** for transcription, two specialized agents built with **LangChain** for contextualization and extraction, **Pydantic** for output validation, and **Langfuse** for observability. Orchestration consists of direct sequential calls in Python.

[Architecture](#architecture) · [Example Output](#example-output) · [Installation](#installation) · [Usage](#usage) · [Current Limitations](#current-limitations)

## What it does

1. Receives one image of the original contract and one image of its amendment.
2. Transcribes each image using GPT-4o Vision through the OpenAI Responses API.
3. Builds a contextual map of document sections, their purposes, and their correspondence.
4. Passes the map and both source texts to an extraction agent to identify additions, removals, and modifications.
5. Validates the response against a Pydantic model and prints the result as JSON.
6. Records the execution stages in Langfuse, including their inputs, outputs, and timing.

## Tech Stack

| Technology | Role |
| --- | --- |
| Python 3.10+ | CLI, configuration, and sequential orchestration. |
| OpenAI GPT-4o / Vision | Image transcription and text analysis. |
| OpenAI Python SDK / Responses API | Sends document images for transcription. |
| LangChain (`langchain-core`, `langchain-openai`) | Prompt composition, `ChatOpenAI` calls, and structured extraction. |
| Pydantic | Defines and validates the output schema. |
| Langfuse Python SDK v4 | Stage observations and LangChain callbacks. |
| Pillow | Checks that input images can be decoded. |
| python-dotenv | Loads credentials from `.env`. |

Direct dependency versions are pinned in [`requirements.txt`](requirements.txt).

## Architecture

```text
Original contract image --> GPT-4o Vision --> original text
Amendment image ---------> GPT-4o Vision --> amendment text

                       both source texts
                               |
                               v
                   Contextualization Agent
                               |
                               v
                Context map + both source texts
                               |
                               v
                      Extraction Agent
                               |
                               v
               ContractChangeOutput (Pydantic)
                               |
                               v
                         JSON in CLI
```

[`src/main.py`](src/main.py) coordinates every step sequentially. Langfuse observes the workflow and the agents' LangChain calls; it does not control execution.

## Example Output

Recorded CLI output for the included `simple` case, dated September 17, 2026. The example is preserved from the existing project documentation in Spanish to match the source documents and recorded response.

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

The CLI prints `--- RESULTADO FINAL ---` before the JSON. Wording may vary between runs; the result is printed to the console and is not automatically saved to a file.

## Key Engineering Decisions

### Separate transcription from reasoning

Both images are transcribed before the agents run. This keeps source text available throughout the comparison and separates image interpretation from structural mapping and change extraction.

### Separate contextualization from extraction

The contextualization agent maps sections and their relationships without identifying changes. The extraction agent handles the comparison and receives both transcriptions alongside that map. Each prompt has a focused responsibility, and extraction can check the source texts rather than relying only on an intermediate interpretation.

### Structured outputs with Pydantic

The extractor uses `with_structured_output(ContractChangeOutput)` to enforce a predictable output contract. Pydantic validates structure and types, rejects extra fields, and strips surrounding whitespace from strings. It does not validate the factual correctness of the analysis.

### Reduce agent variability

Both agents use `gpt-4o` with `temperature=0` to reduce response variability. This does not guarantee identical or error-free results. The separate Vision transcription call does not explicitly set a temperature.

### Observability with Langfuse

Named observations separate transcription, contextualization, and extraction, making their inputs, outputs, and latency inspectable. LangChain callbacks add prompt and response visibility for the agents; the parser explicitly attaches token usage when OpenAI returns it.

### Sequential orchestration instead of LangGraph

The workflow is linear, with no dynamic routing, agent branching, or cycles. Direct calls keep the orchestration proportional to that scope and make execution order explicit. The application does not use LangGraph to orchestrate its agents.

## How it works

### Image transcription

[`src/image_parser.py`](src/image_parser.py) accepts PNG, JPG, and JPEG files. Before each transcription request, it checks the path, extension, file size, and image integrity using Pillow. The per-file size limit is **10 MiB** (`10 * 1024 * 1024` bytes).

The parser encodes the image as a Base64 data URL and calls `client.responses.create()` with `detail="high"`. Its prompt requests all visible text in document order, preserving headings, clause numbering, names, dates, and amounts without summarizing or interpreting them.

### Contextualization

[`contextualize_contracts`](src/agents/contextualization_agent.py) receives both transcriptions and produces a textual map of each document's sections, their purposes, and their correspondence. Its prompt explicitly excludes comparing values or describing contractual changes.

### Change extraction

[`extract_changes`](src/agents/extraction_agent.py) receives both transcriptions and the context map. Its prompt asks for additions, removals, and modifications, checked against the source texts, without inferring legal consequences or intentions unsupported by the documents.

### Structured output

[`ContractChangeOutput`](src/models.py) defines three required fields:

| Field | Type | Content |
| --- | --- | --- |
| `sections_changed` | `list[str]` | Affected clauses or sections. |
| `topics_touched` | `list[str]` | Affected contractual topics. |
| `summary_of_the_change` | `str` | Factual summary of the detected changes. |

The extraction chain returns a Pydantic instance, which the CLI serializes with `model_dump_json(indent=2)`. Change types are described in the summary; the schema does not define a separate record or type field for each change.

## Installation

### Prerequisites

- Python **3.10 or newer**, within the Python 3 series, and `pip`.
- An OpenAI API key with access to `gpt-4o`.
- A Langfuse project with a public key, secret key, and its region or instance URL.
- Network access to OpenAI and Langfuse.

Run all commands from the project root (`m4/project` in this workspace).

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure credentials

Copy [`.env.example`](.env.example) to `.env` and fill in the values. Keep an existing configured `.env` rather than overwriting it.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS / Linux:

```bash
cp .env.example .env
```

```dotenv
OPENAI_API_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

All three keys are required by the current configuration. Set `LANGFUSE_HOST` to the URL for your Langfuse project's region or instance; the application passes it to the SDK as `base_url`. The default is `https://cloud.langfuse.com`. The `.env` file is excluded from Git by [`.gitignore`](.gitignore).

### Runtime defaults

| Setting | Vision transcription | Each specialized agent |
| --- | --- | --- |
| Model | `gpt-4o` | `gpt-4o` |
| Timeout per request | 60 seconds | 60 seconds |
| Maximum retries | 2 | 2 |
| Output token limit per call | 6000 | 2000 |
| Temperature | Not explicitly set | `0` |

Parser defaults are defined in [`Settings`](src/config.py); agent settings are defined in their respective modules. Only the credentials and Langfuse host shown above are read from environment variables by `Settings.from_env()`.

## Usage

With the virtual environment active and credentials configured:

### Simple test case

```bash
python -m src.main --case simple
```

### Complex test case

```bash
python -m src.main --case complex
```

### Custom document images

Pass the original contract first and its amendment second:

```bash
python -m src.main "path/to/original.png" "path/to/amendment.png"
```

Each analysis makes real OpenAI API calls and incurs API usage. The CLI accepts one image per document and prints the JSON result described in [Example Output](#example-output).

## Observability

[`LangfuseObservability`](src/observability.py) initializes the Langfuse client using the project settings. A complete execution creates this observation hierarchy:

```text
contract-analysis                [chain]
├── parse_original_contract      [generation]
├── parse_amendment_contract     [generation]
├── contextualization_agent      [span]
└── extraction_agent             [span]
```

The agents receive a Langfuse `CallbackHandler`, which adds observations for their internal LangChain operations. The full trace can therefore contain additional nested nodes.

The instrumentation captures:

- Image paths at the root and transcription stages.
- Transcribed text, the context map, and the final result at their respective stages.
- Agent chain inputs and outputs, including prompts and responses through LangChain callbacks.
- Observation timing and stage metadata.
- Model and token usage: explicitly attached by the parser when OpenAI returns `usage`, and captured through callbacks for the agents.

The Vision observations record image paths and extracted text; they do not explicitly record the transcription prompt or image payload. Images are sent to OpenAI, while document text and analysis results are recorded in Langfuse.

The application does not submit a manually calculated monetary cost. Langfuse can infer costs when the model and usage fields match a priced model definition; availability depends on that configuration. See [Langfuse token and cost tracking](https://langfuse.com/docs/observability/features/token-and-cost-tracking).

Find executions by the name `contract-analysis` in your Langfuse project. The CLI flushes pending observations in a `finally` block after closing them, including when an analysis stage fails.

## Validation and Error Handling

Application-specific exceptions are defined in [`src/errors.py`](src/errors.py).

| Area | Checks or errors handled |
| --- | --- |
| Configuration | Missing required OpenAI or Langfuse keys. |
| Images | Missing paths, non-file paths, unsupported extensions, empty files, corrupt or undecodable images, and files larger than 10 MiB. |
| Vision transcription | OpenAI timeouts, rate limits, connection errors, HTTP API errors, and empty text responses. |
| Structured extraction | Pydantic `ValidationError`, wrapped as `ContractOutputValidationError`. |
| Observability | Exceptions propagated during client initialization or `flush()`, wrapped as `ObservabilityError`. |

For errors it catches, the CLI prints `Error:` followed by a message and exits with status `1`. OpenAI-specific exception translation is implemented in the image parser; agent API failures do not have equivalent handling. The prompts guide transcription and comparison behavior but cannot guarantee correctness.

## Testing / Evaluation

Two document pairs are included in [`data/test_contracts/`](data/test_contracts/README.md). Each case contains `contrato_original.png`, `adenda.png`, and `expected.json`.

| CLI case | Directory | Expected changes |
| --- | --- | --- |
| `simple` | [`caso_simple`](data/test_contracts/caso_simple) | Monthly fee increases from USD 1,000 to USD 1,500; expiration moves from December 31, 2026 to June 30, 2027. |
| `complex` | [`caso_complejo`](data/test_contracts/caso_complejo) | Territorial scope expands from Argentina and Uruguay to also include Chile and Paraguay; a restriction limiting confidential information use to evaluating a financing transaction is removed; a duty to notify security incidents within 24 hours of detection is added. |

The `expected.json` files are **manual review references**. The CLI does not load them, compare results automatically, or calculate accuracy, precision, or a pass/fail score. There is no automated test suite or evaluation runner in the repository.

To review a case, run its [usage command](#usage), check the transcription and analysis stages in Langfuse, and compare the affected sections, topics, and factual changes with its reference and source images. Exact wording is not a matching criterion.

## Current Limitations

- **One image per document.** The CLI does not natively process PDFs or combine multiple pages.
- **Original contract plus amendment.** The current prompts and interface target that relationship; arbitrary document comparison is outside the documented scope.
- **Structure is not factual validation.** Pydantic checks the response schema and types, not whether every change is correct or complete.
- **Human verification is required.** Transcription errors can propagate into extraction, and both stages require review. The pipeline does not replace human legal review.
- **Evaluation is manual.** The two included cases do not establish measured accuracy or broader reliability.
- **Finite output budgets.** Vision transcription is capped at 6000 output tokens and each agent at 2000; the workflow does not split long documents or explicitly check for truncated responses.

## Project Structure

```text
.
├── README.md
├── requirements.txt
├── .env.example
├── src/
│   ├── main.py                       # CLI and sequential workflow
│   ├── config.py                     # Credentials and parser defaults
│   ├── image_parser.py               # Image validation and transcription
│   ├── models.py                     # Pydantic output schema
│   ├── observability.py              # Langfuse client and callbacks
│   ├── errors.py                     # Application-specific exceptions
│   └── agents/
│       ├── contextualization_agent.py
│       └── extraction_agent.py
└── data/test_contracts/
    ├── README.md
    ├── caso_simple/                   # Original, amendment, expected JSON
    └── caso_complejo/                 # Original, amendment, expected JSON
```

Developed as the Module 4 final project for an AI Engineering program.

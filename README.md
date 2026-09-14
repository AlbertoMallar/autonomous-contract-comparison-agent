# Autonomous Contract Comparison Agent

Proyecto Integrador del Módulo 4 de AI Engineering.

Sistema multiagente para analizar un contrato original y su adenda a partir de imágenes y detectar los cambios introducidos.

## Arquitectura actual

El pipeline implementado es:

1. `image_parser.py`
   - recibe una imagen del contrato;
   - la codifica en Base64;
   - utiliza GPT-4o Vision para extraer fielmente su texto.

2. `ContextualizationAgent`
   - recibe el contrato original y la adenda ya convertidos a texto;
   - identifica su estructura, secciones y correspondencias;
   - genera un mapa contextual sin extraer los cambios.

3. `ExtractionAgent`
   - recibe ambos textos y el mapa contextual;
   - identifica modificaciones, eliminaciones y adiciones;
   - devuelve el resultado mediante un modelo Pydantic.

4. `ContractChangeOutput`
   - valida la estructura final con:
     - `sections_changed`
     - `topics_touched`
     - `summary_of_the_change`

## Casos de prueba

Actualmente existen dos pares de documentos:

- `caso_simple`: modificación de monto mensual y vencimiento.
- `caso_complejo`: modificación, eliminación y adición de cláusulas.

Ambos casos fueron procesados exitosamente por el pipeline completo.

## Estado

Esta versión representa el MVP funcional del proyecto.

Próximas etapas:
- validación y manejo de errores;
- soporte más robusto de imágenes;
- integración con Langfuse;
- argumentos de línea de comandos;
- documentación y preparación de la demo final.
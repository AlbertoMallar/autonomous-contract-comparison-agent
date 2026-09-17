# Casos de prueba

Este directorio contiene los documentos utilizados para validar el pipeline.

## caso_simple

Caso base con dos modificaciones:

- cambio del monto mensual;
- cambio de la fecha de vencimiento.

Archivos:

- `contrato_original.png`
- `adenda.png`
- `expected.json`

## caso_complejo

Caso con distintos tipos de cambio contractual:

- modificación del alcance territorial;
- eliminación de una restricción de uso;
- adición de una cláusula de seguridad de la información.

Archivos:

- `contrato_original.png`
- `adenda.png`
- `expected.json`

Los archivos `expected.json` funcionan como referencia para verificar manualmente que el resultado del pipeline identifique correctamente los cambios esperados.
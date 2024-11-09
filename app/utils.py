import ell
import os
from dotenv import load_dotenv
import json

load_dotenv()


@ell.complex(model="gpt-4o-mini")
def procesar_historia(historia_actual: str, texto_bruto: str) -> str:
    return f"""
Historia actual:
{historia_actual}

Nuevo texto en bruto:
{texto_bruto}

Por favor, genera una historia clínica actualizada y coherente.
"""


@ell.complex(model="gpt-4o-mini")
def procesar_detalle_atencion(
    historia_paciente: str, detalle_actual: str, texto_bruto: str
) -> str:
    return f"""
Usted es un especialista en medicina de urgencias y emergencias y en documentación clínica. Su tarea es elaborar un registro en tiempo real del proceso de atención de un paciente en un servicio de urgencias, basándose en la información proporcionada y siguiendo los principios de documentación en medicina de emergencia.

Se le proporcionará la siguiente información:

<historia>
{historia_paciente}
</historia>

<atencion_actual>
{detalle_actual}
</atencion_actual>

<nuevo_texto_atencion>
{texto_bruto}
</nuevo_texto_atencion>

Utilice esta información para generar un registro incremental del proceso de atención, siguiendo estos principios y guías:

A. Principios fundamentales de la documentación en medicina de emergencia:
1. Reconocimiento y manejo inmediato de condiciones que amenazan la vida
2. Enfoque sistemático
3. Estratificación dinámica del riesgo

Basándose en estos principios y en la información proporcionada, genere un registro incremental del proceso de atención. Asegúrese de:

1. Utilizar español médico chileno conciso. La redacción debe ser simple, clara, directa. Sin marcas markdown. solo texto plano. Tratar de presentar textos fluidos
2. Seguir un orden cronológico en la documentación.
3. Enfocarse en los aspectos más críticos y relevantes de la atención del paciente.
4. Incluir todas las evaluaciones, intervenciones y decisiones clínicas importantes.
5. Documentar cualquier cambio significativo en el estado del paciente.
6. Usa abreviaciones médicas reconocidas y universales
7. Evita justificaciones, interpretaciones y recomendaciones

Presente su registro incremental dentro de etiquetas <registro_atencion>.
"""


@ell.complex(model="gpt-4o-mini")
def procesar_texto_no_estructurado(texto_bruto: str):
    return f"""
Usted es un asistente que extrae información médica de texto no estructurado.

Por favor, extraiga y devuelva los siguientes datos en formato JSON:
- run: RUN del paciente (formato '12345678-9').
- nombre: Nombre completo del paciente.
- fecha_nacimiento: Fecha de nacimiento en formato dd/mm/aaaa.

Si algún dato no está presente, coloque 'N/A' en su lugar.

Texto:
{texto_bruto}
"""

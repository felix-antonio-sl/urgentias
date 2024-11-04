import ell
import os
from dotenv import load_dotenv

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
def procesar_detalle_atencion(historia_paciente: str, detalle_actual: str, texto_bruto: str) -> str:
    return f"""
Historia del paciente:
{historia_paciente}

Detalle actual de la atención:
{detalle_actual}

Nuevo texto en bruto:
{texto_bruto}

Por favor, genera un detalle de atención actualizado y coherente. la idea es ir entendiendo que se hace y que le pasa al paciente durante la atencion
"""

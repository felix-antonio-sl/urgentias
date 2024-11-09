import os
import ell
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import logging

load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definición de modelos de salida estructurados
class DiagnosticoDiferencial(BaseModel):
    diagnosticos: list[str] = Field(description="Lista de posibles diagnósticos diferenciales.")

class ManejoSugerido(BaseModel):
    manejo: str = Field(description="Recomendaciones de manejo clínico.")

class ProximaAccion(BaseModel):
    accion: str = Field(description="Próxima acción más importante a realizar.")

class Alertas(BaseModel):
    alertas: list[str] = Field(description="Lista de amenazas o riesgos identificados.")

# Funciones AI utilizando ell con mensajes estructurados
@ell.complex(model="gpt-4o-mini", response_format=DiagnosticoDiferencial)
def generar_diagnostico_diferencial(historia_paciente: str, detalle_atencion: str):
    """Eres un médico de emergencias experto en diagnóstico diferencial."""
    return [
        ell.user(f"""
Basándote en la siguiente información, proporciona una lista de posibles diagnósticos diferenciales:

Historia Clínica:
{historia_paciente}

Detalle de Atención:
{detalle_atencion}

Responde en formato JSON con el siguiente esquema:
{json.dumps(DiagnosticoDiferencial.model_json_schema(), indent=2)}
""")
    ]

@ell.complex(model="gpt-4o-mini", response_format=ManejoSugerido)
def generar_manejo_sugerido(historia_paciente: str, detalle_atencion: str):
    """Eres un médico de emergencias experto en manejo clínico."""
    return [
        ell.user(f"""
Basándote en la siguiente información, proporciona recomendaciones de manejo alineadas con las guías actuales:

Historia Clínica:
{historia_paciente}

Detalle de Atención:
{detalle_atencion}

Responde en formato JSON con el siguiente esquema:
{json.dumps(ManejoSugerido.model_json_schema(), indent=2)}
""")
    ]

@ell.complex(model="gpt-4o-mini", response_format=ProximaAccion)
def generar_proxima_accion(historia_paciente: str, detalle_atencion: str):
    """Eres un médico de emergencias priorizando acciones clínicas."""
    return [
        ell.user(f"""
Basándote en la siguiente información, indica la próxima acción más importante:

Historia Clínica:
{historia_paciente}

Detalle de Atención:
{detalle_atencion}

Responde en formato JSON con el siguiente esquema:
{json.dumps(ProximaAccion.model_json_schema(), indent=2)}
""")
    ]

@ell.complex(model="gpt-4o-mini", response_format=Alertas)
def generar_alertas(historia_paciente: str, detalle_atencion: str):
    """Eres un médico de emergencias atento a posibles riesgos."""
    return [
        ell.user(f"""
Basándote en la siguiente información, proporciona una lista de posibles amenazas o riesgos:

Historia Clínica:
{historia_paciente}

Detalle de Atención:
{detalle_atencion}

Responde en formato JSON con el siguiente esquema:
{json.dumps(Alertas.model_json_schema(), indent=2)}
""")
    ]

# Funciones auxiliares existentes
def load_prompt(filename):
    """Carga un prompt desde un archivo en el directorio prompts."""
    base_dir = os.path.dirname(__file__)
    prompt_path = os.path.join(base_dir, "prompts", filename)
    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()

@ell.complex(model="gpt-4o-mini")
def procesar_historia(historia_actual: str, texto_bruto: str):
    """Procesa la historia clínica actualizada."""
    prompt_template = load_prompt("procesar_historia.txt")
    prompt_content = prompt_template.format(
        historia_actual=historia_actual, texto_bruto=texto_bruto
    )
    return [ell.user(prompt_content)]

@ell.complex(model="gpt-4o-mini")
def procesar_detalle_atencion(
    historia_paciente: str, detalle_actual: str, texto_bruto: str
):
    """Procesa el detalle de atención del paciente."""
    prompt_template = load_prompt("procesar_detalle_atencion.txt")
    prompt_content = prompt_template.format(
        historia_paciente=historia_paciente,
        detalle_actual=detalle_actual,
        texto_bruto=texto_bruto,
    )
    return [ell.user(prompt_content)]


@ell.complex(model="gpt-4o-mini")
def procesar_texto_no_estructurado(texto_bruto: str):
    """Extrae información médica de texto no estructurado."""
    prompt_template = load_prompt("procesar_texto_no_estructurado.txt")
    prompt_content = prompt_template.format(texto_bruto=texto_bruto)
    return [ell.user(prompt_content)]
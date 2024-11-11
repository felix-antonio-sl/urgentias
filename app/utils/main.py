import os
import ell
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import logging
from flask import current_app
from typing import List

load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Definición del modelo de salida estructurada unificada
class AsistenciaMedica(BaseModel):
    diagnostico_diferencial: List[str] = Field(
        description="Lista de posibles diagnósticos diferenciales."
    )
    manejo_sugerido: str = Field(description="Recomendaciones de manejo clínico.")
    proxima_accion: str = Field(description="Próxima acción más importante a realizar.")
    alertas: List[str] = Field(description="Lista de amenazas o riesgos identificados.")


@ell.complex(model="gpt-4o-mini", response_format=AsistenciaMedica)
def generar_asistencia_medica_ia(historia_conocida: str, atencion_en_curso: str):
    """Eres un médico de emergencias experto en diagnóstico y manejo clínico."""
    prompt_template = load_prompt("generar_asistencia_medica.txt")
    prompt_content = prompt_template.format(
        historia_conocida=historia_conocida,
        atencion_en_curso=atencion_en_curso,
        json_schema=json.dumps(AsistenciaMedica.model_json_schema(), indent=2),
    )
    return [ell.user(prompt_content)]


@ell.complex(model="gpt-4o-mini")
def agregar_nuevos_antecedentes_ia(historia_conocida: str, nuevos_antecedentes: str):
    prompt_template = load_prompt("agregar_antecedentes_medicos.txt")
    prompt_content = prompt_template.format(
        historia_conocida=historia_conocida, nuevos_antecedentes=nuevos_antecedentes
    )
    return [ell.user(prompt_content)]


@ell.complex(model="gpt-4o-mini")
def agregar_novedades_atencion_ia(
    historia_conocida: str, atencion_hasta_ahora: str, novedades_atencion: str
):
    prompt_template = load_prompt("agregar_novedades_atencion.txt")
    prompt_content = prompt_template.format(
        historia_conocida=historia_conocida,
        atencion_hasta_ahora=atencion_hasta_ahora,
        novedades_atencion=novedades_atencion,
    )
    return [ell.user(prompt_content)]


@ell.complex(model="gpt-4o-mini")
def extraer_datos_inicio_paciente_ia(datos_inicio_paciente: str):
    prompt_template = load_prompt("extraer_datos_paciente.txt")
    prompt_content = prompt_template.format(datos_inicio_paciente=datos_inicio_paciente)
    return [ell.user(prompt_content)]


@ell.complex(model="gpt-4o-mini")
def generar_reporte_atencion_ia(
    historia_conocida: str, atencion_en_curso: str, tipo_reporte: str
):
    valid_report_types = {
        "alta_ambulatoria": "generar_reporte_alta_ambulatoria.txt",
        "hospitalizacion": "generar_reporte_hospitalizacion.txt",
        "interconsulta": "generar_reporte_interconsulta.txt",
    }

    if tipo_reporte not in valid_report_types:
        raise ValueError(f"Tipo de reporte no válido: {tipo_reporte}")

    prompt_filename = valid_report_types[tipo_reporte]
    prompt_template = load_prompt(prompt_filename)
    prompt_content = prompt_template.format(
        historia_conocida=historia_conocida, atencion_en_curso=atencion_en_curso
    )

    return [ell.user(prompt_content)]


# Funciones auxiliares existentes
def load_prompt(filename):
    """Carga un prompt desde el directorio configurado en PROMPT_DIR."""
    prompt_dir = current_app.config.get("PROMPT_DIR", "./static/prompts")
    prompt_path = os.path.join(prompt_dir, filename)

    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()

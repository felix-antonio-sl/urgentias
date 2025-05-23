import os
import json
import logging
from dataclasses import dataclass
from typing import List, Optional, Any

from dotenv import load_dotenv
from flask import current_app
from pydantic import BaseModel, Field
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AIResult:
    """Simple container for LLM results."""
    content: str
    parsed: Optional[Any] = None

    @property
    def text(self) -> str:
        return self.content


# Definición del modelo de salida estructurada unificada
class AsistenciaMedica(BaseModel):
    diagnostico_diferencial: List[str] = Field(
        description="Lista de posibles diagnósticos diferenciales."
    )
    manejo_sugerido: str = Field(description="Recomendaciones de manejo clínico.")
    proxima_accion: str = Field(description="Próxima acción más importante a realizar.")
    alertas: List[str] = Field(description="Lista de amenazas o riesgos identificados.")


def _create_chat(model: Optional[str] = None) -> ChatOpenAI:
    cfg = current_app.config
    return ChatOpenAI(
        api_key=cfg.get("DEEPSEEK_API_KEY"),
        base_url=cfg.get("DEEPSEEK_API_BASE"),
        model=model or cfg.get("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=0.0,
    )


def generar_asistencia_medica_ia(historia_conocida: str, atencion_en_curso: str) -> AIResult:
    """Genera recomendaciones médicas estructuradas."""
    parser = PydanticOutputParser(pydantic_object=AsistenciaMedica)
    prompt_text = load_prompt("generar_asistencia_medica.txt")
    prompt = PromptTemplate(
        template=prompt_text,
        input_variables=["historia_conocida", "atencion_en_curso", "json_schema"],
    )
    chain = prompt | _create_chat()
    message = chain.invoke(
        {
            "historia_conocida": historia_conocida,
            "atencion_en_curso": atencion_en_curso,
            "json_schema": json.dumps(AsistenciaMedica.model_json_schema(), indent=2),
        }
    )
    parsed = None
    try:
        parsed = parser.parse(message.content)
    except Exception as e:
        logger.error(f"Error parsing asistencia medica: {e}")
    return AIResult(content=message.content, parsed=parsed)


def agregar_nuevos_antecedentes_ia(historia_conocida: str, nuevos_antecedentes: str) -> AIResult:
    prompt_text = load_prompt("agregar_antecedentes_medicos.txt")
    prompt = PromptTemplate(
        template=prompt_text,
        input_variables=["historia_conocida", "nuevos_antecedentes"],
    )
    chain = prompt | _create_chat()
    message = chain.invoke(
        {
            "historia_conocida": historia_conocida,
            "nuevos_antecedentes": nuevos_antecedentes,
        }
    )
    return AIResult(content=message.content)


def agregar_novedades_atencion_ia(
    historia_conocida: str, atencion_hasta_ahora: str, novedades_atencion: str
) -> AIResult:
    prompt_text = load_prompt("agregar_novedades_atencion.txt")
    prompt = PromptTemplate(
        template=prompt_text,
        input_variables=["historia_conocida", "atencion_hasta_ahora", "novedades_atencion"],
    )
    chain = prompt | _create_chat()
    message = chain.invoke(
        {
            "historia_conocida": historia_conocida,
            "atencion_hasta_ahora": atencion_hasta_ahora,
            "novedades_atencion": novedades_atencion,
        }
    )
    return AIResult(content=message.content)


def extraer_datos_inicio_paciente_ia(datos_inicio_paciente: str) -> AIResult:
    prompt_text = load_prompt("extraer_datos_paciente.txt")
    prompt = PromptTemplate(
        template=prompt_text,
        input_variables=["datos_inicio_paciente"],
    )
    chain = prompt | _create_chat()
    message = chain.invoke({"datos_inicio_paciente": datos_inicio_paciente})
    return AIResult(content=message.content)


def generar_reporte_atencion_ia(
    historia_conocida: str, atencion_en_curso: str, tipo_reporte: str
) -> AIResult:
    valid_report_types = {
        "alta_ambulatoria": "generar_reporte_alta_ambulatoria.txt",
        "hospitalizacion": "generar_reporte_hospitalizacion.txt",
        "interconsulta": "generar_reporte_interconsulta.txt",
    }

    if tipo_reporte not in valid_report_types:
        raise ValueError(f"Tipo de reporte no válido: {tipo_reporte}")

    prompt_filename = valid_report_types[tipo_reporte]
    prompt_text = load_prompt(prompt_filename)
    prompt = PromptTemplate(
        template=prompt_text,
        input_variables=["historia_conocida", "atencion_en_curso"],
    )
    chain = prompt | _create_chat()
    message = chain.invoke(
        {
            "historia_conocida": historia_conocida,
            "atencion_en_curso": atencion_en_curso,
        }
    )
    return AIResult(content=message.content)


# Funciones auxiliares existentes
def load_prompt(filename):
    """Carga un prompt desde el directorio configurado en PROMPT_DIR."""
    prompt_dir = current_app.config.get("PROMPT_DIR", "./static/prompts")
    prompt_path = os.path.join(prompt_dir, filename)

    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read()

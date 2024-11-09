import os
import ell
from dotenv import load_dotenv

load_dotenv()

def load_prompt(filename):
    """Carga un prompt desde un archivo en el directorio prompts."""
    base_dir = os.path.dirname(__file__)  # Directorio actual
    prompt_path = os.path.join(base_dir, 'prompts', filename)
    with open(prompt_path, 'r', encoding='utf-8') as file:
        return file.read()

@ell.complex(model="gpt-4o-mini")
def procesar_historia(historia_actual: str, texto_bruto: str):
    """Procesa la historia clínica actualizada."""
    prompt_template = load_prompt('procesar_historia.txt')
    prompt_content = prompt_template.format(
        historia_actual=historia_actual,
        texto_bruto=texto_bruto
    )
    return [ell.user(prompt_content)]

@ell.complex(model="gpt-4o-mini")
def procesar_detalle_atencion(historia_paciente: str, detalle_actual: str, texto_bruto: str):
    """Procesa el detalle de atención del paciente."""
    prompt_template = load_prompt('procesar_detalle_atencion.txt')
    prompt_content = prompt_template.format(
        historia_paciente=historia_paciente,
        detalle_actual=detalle_actual,
        texto_bruto=texto_bruto
    )
    return [ell.user(prompt_content)]

@ell.complex(model="gpt-4o-mini")
def procesar_texto_no_estructurado(texto_bruto: str):
    """Extrae información médica de texto no estructurado."""
    prompt_template = load_prompt('procesar_texto_no_estructurado.txt')
    prompt_content = prompt_template.format(
        texto_bruto=texto_bruto
    )
    return [ell.user(prompt_content)]

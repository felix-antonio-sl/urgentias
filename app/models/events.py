from sqlalchemy import event
from app.extensions import db
from . import Paciente, Atencion
from ..utils import generar_asistencia_medica_ia
import logging

logger = logging.getLogger(__name__)

def actualizar_asistencia_medica(atencion):
    try:
        logger.info(f"Actualizando asistencia médica para Atencion ID: {atencion.id}")
        paciente = atencion.paciente
        logger.debug(f"Historia del Paciente ID {paciente.id}: {paciente.historia}")
        logger.debug(f"Detalle de Atencion ID {atencion.id}: {atencion.detalle}")

        asistencia_msg = generar_asistencia_medica_ia(
            paciente.historia or "", 
            atencion.detalle or ""
        )
        logger.debug(f"Respuesta de AI: {asistencia_msg}")

        if not hasattr(asistencia_msg, 'parsed'):
            logger.error("La respuesta de IA no tiene el atributo 'parsed'")
            raise ValueError("La respuesta de IA no tiene el formato esperado")
            
        atencion.diagnostico_diferencial = "\n".join(
            asistencia_msg.parsed.diagnostico_diferencial
        )
        atencion.manejo_sugerido = asistencia_msg.parsed.manejo_sugerido
        atencion.proxima_accion = asistencia_msg.parsed.proxima_accion
        atencion.alertas = "\n".join(asistencia_msg.parsed.alertas)

        logger.info(f"Asistencia médica actualizada para Atencion ID: {atencion.id}")

    except Exception as e:
        logger.error(f"Error al actualizar asistencia médica para Atencion ID {atencion.id}: {e}", exc_info=True)

@event.listens_for(Paciente.historia, 'set')
def historia_changed(target, value, oldvalue, initiator):
    if value != oldvalue:
        for atencion in target.atenciones:
            if atencion.activa:
                actualizar_asistencia_medica(atencion)

@event.listens_for(Atencion.detalle, 'set')
def detalle_changed(target, value, oldvalue, initiator):
    if value != oldvalue and target.activa:
        actualizar_asistencia_medica(target)

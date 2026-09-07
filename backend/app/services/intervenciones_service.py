import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinico import Alerta, Evento, Intervencion
from app.models.enums import EstadoAlerta, TipoEvento
from app.schemas.intervenciones import IntervencionCrear
from temporal.client import get_temporal_client
from temporal.workflows import AlertaWorkflow


async def registrar_intervencion(
    db: AsyncSession,
    alerta_id: uuid.UUID,
    datos: IntervencionCrear,
    usuario_id: uuid.UUID,
) -> Intervencion:
    """
    Registra el evento clínico de la intervención y le avisa al
    AlertaWorkflow correspondiente. El cambio de estado.estado de la
    alerta a "resuelta" YA NO pasa acá -- lo hace la Activity
    notificar_resolucion, dentro de Temporal.
    """
    alerta = await db.get(Alerta, alerta_id)
    if alerta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe una alerta con id '{alerta_id}'.",
        )

    if alerta.estado == EstadoAlerta.resuelta:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta alerta ya fue resuelta.",
        )

    nueva_intervencion = Intervencion(
        id=uuid.uuid4(),
        alerta_id=alerta_id,
        usuario_id=usuario_id,
        accion=datos.accion,
        observaciones=datos.observaciones,
        finalizada_en=datetime.now(timezone.utc),
    )
    db.add(nueva_intervencion)

    db.add(Evento(
        paciente_id=alerta.paciente_id,
        tipo=TipoEvento.intervencion_registrada,
        descripcion=f"Intervención registrada: {datos.accion}",
        severidad=alerta.severidad,
    ))

    await db.commit()
    await db.refresh(nueva_intervencion)

    if alerta.workflow_id_temporal is not None:
        try:
            client = await get_temporal_client()
            handle = client.get_workflow_handle(alerta.workflow_id_temporal)
            await handle.signal(
                AlertaWorkflow.registrar_intervencion_finalizada,
                args=[datos.accion, datos.observaciones],
            )
        except Exception as error:
            print(f"No se pudo notificar al workflow de la alerta {alerta_id}: {error}")

    return nueva_intervencion
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.temporal_client import resolver_alerta_workflow
from app.models.clinico import Alerta, Evento, Intervencion
from app.models.enums import EstadoAlerta, TipoEvento
from app.schemas.intervenciones import IntervencionCrear


async def obtener_alerta(db: AsyncSession, alerta_id: uuid.UUID) -> Alerta:
    """Devuelve una alerta puntual con sus intervenciones cargadas, o 404."""
    alerta = await db.scalar(
        select(Alerta)
        .where(Alerta.id == alerta_id)
        .options(selectinload(Alerta.intervenciones))
    )
    if alerta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe una alerta con id '{alerta_id}'.",
        )
    return alerta


async def listar_alertas(
    db: AsyncSession,
    paciente_id: uuid.UUID | None = None,
    estado: EstadoAlerta | None = None,
) -> list[Alerta]:
    """
    Lista alertas, más recientes primero. Sin filtros devuelve todas
    (pensado sobre todo para paciente_id=... y/o estado=activa, sirve
    también para probar el endpoint de intervenciones desde Swagger sin
    tener que ir a buscar el id de la alerta directamente en la base).
    """
    consulta = select(Alerta).order_by(Alerta.creada_en.desc())
    if paciente_id is not None:
        consulta = consulta.where(Alerta.paciente_id == paciente_id)
    if estado is not None:
        consulta = consulta.where(Alerta.estado == estado)

    resultado = await db.execute(consulta)
    return list(resultado.scalars().all())


async def registrar_intervencion(
    db: AsyncSession,
    alerta_id: uuid.UUID,
    usuario_id: uuid.UUID,
    datos: IntervencionCrear,
) -> Intervencion:
    """
    Registra la Intervencion que CIERRA una alerta.

    Según la definición del MVP, esta es la ÚNICA forma en la que una
    alerta pasa a "resuelta" -- que el signo vital se haya normalizado
    (Alerta.normalizada_en != None, seteado por el AlertaWorkflow de
    Temporal tras 10 segundos sostenidos) es una condición necesaria
    para que tenga sentido cerrarla, pero NUNCA suficiente por sí sola:
    siempre hace falta que el personal la registre acá.

    Es de "un solo paso": iniciada_en y finalizada_en quedan iguales, no
    hay un estado intermedio de intervención "en curso" separado del de
    la alerta.
    """
    alerta = await obtener_alerta(db, alerta_id)

    if alerta.estado == EstadoAlerta.resuelta:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta alerta ya fue resuelta.",
        )

    nueva_intervencion = Intervencion(
        id=uuid.uuid4(),
        alerta_id=alerta.id,
        usuario_id=usuario_id,
        accion=datos.accion,
        observaciones=datos.observaciones,
    )
    db.add(nueva_intervencion)
    await db.flush()  # asigna iniciada_en (server_default) antes de copiarlo

    nueva_intervencion.finalizada_en = nueva_intervencion.iniciada_en
    alerta.estado = EstadoAlerta.resuelta
    alerta.resuelta_en = nueva_intervencion.iniciada_en

    db.add(Evento(
        paciente_id=alerta.paciente_id,
        tipo=TipoEvento.intervencion_registrada,
        descripcion=f"Intervención registrada: {datos.accion}",
        severidad=alerta.severidad,
    ))

    await db.commit()
    await db.refresh(nueva_intervencion)
    await db.refresh(alerta)

    # Recién después del commit: si Temporal está caído esto no debe
    # impedir cerrar la alerta (ver app/core/temporal_client.py). En el
    # peor caso el workflow correspondiente queda corriendo de más,
    # esperando una señal que nunca le va a llegar -- no afecta a nadie
    # más porque cada workflow está aislado por alerta.
    await resolver_alerta_workflow(alerta.workflow_id_temporal)

    return nueva_intervencion

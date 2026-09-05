import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.temporal_client import (
    iniciar_alerta_workflow,
    senalizar_alerta_workflow,
)
from app.models.clinico import SignoVital, TipoSignoVital
from app.schemas.signos_vitales import SignoVitalCrear
from app.services.deteccion import procesar_nueva_medicion
from app.services.pacientes_service import obtener_paciente


async def registrar_signo_vital(
    db: AsyncSession, paciente_id: uuid.UUID, datos: SignoVitalCrear
) -> dict:
    """
    Registra una medición de signo vital y ejecuta el motor de detección
    de severidad sobre esa medición.

    Todo (medición + evento + alerta + digital twin) se guarda en una
    sola transacción atómica: si algo falla en el medio, no queda una
    medición guardada sin su evaluación de severidad correspondiente.
    """
    await obtener_paciente(db, paciente_id)  # 404 si no existe

    tipo = await db.get(TipoSignoVital, datos.tipo_signo_id)
    if tipo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe un tipo de signo vital con id '{datos.tipo_signo_id}'.",
        )

    nuevo_signo = SignoVital(
        id=uuid.uuid4(),
        paciente_id=paciente_id,
        tipo_signo_id=datos.tipo_signo_id,
        valor=datos.valor,
        origen=datos.origen,
    )
    db.add(nuevo_signo)
    await db.flush()  # asigna medido_en antes de evaluar la severidad

    # --- Punto de integración del motor de detección ---
    resultado_deteccion = await procesar_nueva_medicion(
        db=db,
        paciente_id=paciente_id,
        tipo_signo_id=datos.tipo_signo_id,
        valor=datos.valor,
    )

    await db.commit()
    await db.refresh(nuevo_signo)

    alerta = resultado_deteccion["alerta"]
    if alerta is not None:
        await db.refresh(alerta)

        # Recién ACÁ, después del commit, tocamos Temporal: si algo de
        # lo anterior hubiese fallado y hecho rollback, no queremos un
        # workflow corriendo para una alerta que en Postgres nunca
        # existió. Ambas funciones son best-effort (ver
        # app/core/temporal_client.py): si Temporal está caído, la
        # medición y la alerta ya quedaron guardadas igual, simplemente
        # esa alerta no se va a auto-normalizar hasta que vuelva.
        severidad_str = resultado_deteccion["severidad"].value
        if resultado_deteccion["alerta_es_nueva"]:
            await iniciar_alerta_workflow(
                workflow_id=alerta.workflow_id_temporal,
                alerta_id=str(alerta.id),
                severidad_inicial=severidad_str,
            )
        else:
            await senalizar_alerta_workflow(
                workflow_id=alerta.workflow_id_temporal,
                severidad=severidad_str,
            )

    return {
        "signo_vital": nuevo_signo,
        "severidad_calculada": resultado_deteccion["severidad"],
        "alerta": alerta,
    }


async def listar_signos_vitales_paciente(
    db: AsyncSession, paciente_id: uuid.UUID
) -> list[SignoVital]:
    """Historial de mediciones de un paciente, la más reciente primero."""
    await obtener_paciente(db, paciente_id)

    resultado = await db.execute(
        select(SignoVital)
        .where(SignoVital.paciente_id == paciente_id)
        .order_by(SignoVital.medido_en.desc())
    )
    return list(resultado.scalars().all())

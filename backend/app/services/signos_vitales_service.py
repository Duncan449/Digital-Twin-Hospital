import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinico import SignoVital, TipoSignoVital, Alerta
from app.schemas.signos_vitales import SignoVitalCrear
from app.services.deteccion import procesar_nueva_medicion
from app.services.pacientes_service import obtener_paciente
from app.websockets.eventos import publicar_evento

from temporal.client import get_temporal_client
from temporal.workflows import AlertaWorkflow

TASK_QUEUE = "hospital-task-queue"

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
    
    await publicar_evento(
        paciente_id=str(paciente_id),
        tipo="medicion_registrada",
        data={
            "tipo_signo_id": str(datos.tipo_signo_id),
            "valor": str(nuevo_signo.valor),
            "medido_en": nuevo_signo.medido_en.isoformat(),
            "severidad_calculada": resultado_deteccion["severidad"].value,
        },
    )

    alerta = resultado_deteccion["alerta"]
    if alerta is not None:
        await db.refresh(alerta)
        
        await publicar_evento(
            paciente_id=str(paciente_id),
            tipo=(
                "alerta_generada"
                if resultado_deteccion["alerta_es_nueva"]
                else "alerta_actualizada"
            ),
            data={
                "alerta_id": str(alerta.id),
                "severidad": alerta.severidad.value,
                "valor_detectado": str(alerta.valor_detectado),
                "estado": alerta.estado.value,
            },
        )

        if alerta.workflow_id_temporal is None:
            await _intentar_iniciar_workflow_alerta(db, alerta)

    return {
        "signo_vital": nuevo_signo,
        "severidad_calculada": resultado_deteccion["severidad"],
        "alerta": alerta,
    }


async def _intentar_iniciar_workflow_alerta(db: AsyncSession, alerta: Alerta) -> None:
    try:
        client = await get_temporal_client()
        await client.start_workflow(
            AlertaWorkflow.run,
            str(alerta.id),
            id=str(alerta.id),
            task_queue=TASK_QUEUE,
        )
        alerta.workflow_id_temporal = str(alerta.id)
        await db.commit()
    except Exception as error:
        await db.rollback()
        print(f"No se pudo iniciar el workflow para la alerta {alerta.id}: {error}")

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

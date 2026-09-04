import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinico import SignoVital, TipoSignoVital
from app.schemas.signos_vitales import SignoVitalCrear
from app.services.pacientes_service import obtener_paciente


async def registrar_signo_vital(
    db: AsyncSession, paciente_id: uuid.UUID, datos: SignoVitalCrear
) -> SignoVital:
    """
    Registra una medición de signo vital para un paciente.

    Por ahora no integra el motor de detección de anomalías, ni genera alertas. Solo guarda la medición en la base de datos.
    """
    # Confirma que el paciente existe, lanza 404 si no lo encuentra).
    await obtener_paciente(db, paciente_id)

    # Confirma que el tipo de signo vital existe 
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
    await db.commit()
    await db.refresh(nuevo_signo)
    return nuevo_signo


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

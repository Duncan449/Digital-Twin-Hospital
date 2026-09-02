import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pacientes import DigitalTwin, Paciente
from app.schemas.pacientes import PacienteCrear


async def crear_paciente(db: AsyncSession, datos: PacienteCrear) -> Paciente:
    """
    Crea un Paciente y su DigitalTwin asociado, en una sola transacción.

    Generamos los UUID acá mismo, en Python, ANTES de insertar nada:
    1. Necesitamos el id del paciente para poder armar el DigitalTwin
       (que tiene paciente_id como FK) sin depender de una consulta
       extra a la base para obtener el id generado.
    2. Cuando conectemos Temporal, vamos a reutilizar
       estos mismos UUID para correlacionar "este paciente" con sus
       workflows, de forma determinística e idempotente.
    """
    paciente_id = uuid.uuid4()

    nuevo_paciente = Paciente(
        id=paciente_id,
        nombre=datos.nombre,
        apellido=datos.apellido,
        documento=datos.documento,
        fecha_nacimiento=datos.fecha_nacimiento,
        genero=datos.genero,
        sala=datos.sala,
        cama=datos.cama,
    )

    # severidad_actual y las fechas usan sus defaults del modelo (normal / now()).
    nuevo_digital_twin = DigitalTwin(
        id=uuid.uuid4(),
        paciente_id=paciente_id,
    )

    # Con add() ambos objetos quedan "pendientes" en la sesión, pero
    # todavía no se mandó ningún INSERT a la base.
    db.add(nuevo_paciente)
    db.add(nuevo_digital_twin)

    try:
        # Mandamos los INSERTs a la base en una sola transacción. Si algo falla, se hace rollback y no queda nada insertado.
        await db.commit()
    except IntegrityError:
        # Salta acá, por ejemplo, si el "documento" ya existe (es unique=True).
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un paciente con el documento '{datos.documento}'.",
        )

    # refresh() vuelve a leer la fila desde la base para traer los valores
    # que se generaron ahí (fecha_ingreso, creado_en, actualizado_en, estado). Sin esto, el objeto nuevo_paciente tendría esos campos como None.
    await db.refresh(nuevo_paciente)
    return nuevo_paciente

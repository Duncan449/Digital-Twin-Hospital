import uuid

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinico import Evento
from app.models.enums import EstadoPaciente, TipoEvento
from app.models.pacientes import DigitalTwin, Paciente
from app.schemas.pacientes import PacienteCrear, PacienteActualizar


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


async def listar_pacientes(
    db: AsyncSession, estado: EstadoPaciente = EstadoPaciente.internado
) -> list[Paciente]:
    """
    Lista pacientes filtrados por estado. Por default trae solo los
    internados, pero el frontend puede
    pedir explícitamente los dados_de_alta para una vista de historial.
    """
    resultado = await db.execute(select(Paciente).where(Paciente.estado == estado))
    return list(resultado.scalars().all())


async def obtener_paciente(db: AsyncSession, paciente_id: uuid.UUID) -> Paciente:
    """
    Busca un paciente por id. Lanza 404 si no existe.
    """
    paciente = await db.get(Paciente, paciente_id)
    if paciente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró un paciente con id '{paciente_id}'.",
        )
    return paciente


async def actualizar_paciente(
    db: AsyncSession, paciente_id: uuid.UUID, datos: PacienteActualizar
) -> Paciente:
    """
    Actualización parcial de un paciente. Puede tocar tanto campos
    operativos (sala, cama, genero) como de identidad (nombre, documento,
    etc. para corregir errores de tipeo). Todo cambio queda registrado
    como un Evento, para poder responder "qué cambió, y cuándo"
    """
    paciente = await obtener_paciente(db, paciente_id)

    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        # PATCH con body vacío: no hay nada que hacer ni que registrar.
        return paciente

    # Capturamos el valor "antes" de cada campo que va a cambiar, para
    # que el Evento cuente la historia completa (de qué a qué), no solo
    # el estado final.
    valores_previos = {campo: getattr(paciente, campo) for campo in cambios}

    for campo, valor in cambios.items():
        setattr(paciente, campo, valor)

    evento = Evento(
        paciente_id=paciente_id,
        tipo=TipoEvento.paciente_actualizado,
        descripcion=f"Campos modificados: {valores_previos} -> {cambios}",
    )
    db.add(evento)

    try:
        # Un solo commit para el paciente Y el evento: si algo falla
        # (ej. el nuevo documento ya existe en otro paciente), no queda
        # un evento huérfano registrando un cambio que nunca se aplicó.
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo actualizar el paciente por un conflicto de datos.",
        )

    await db.refresh(paciente)
    return paciente


async def dar_de_alta_paciente(db: AsyncSession, paciente_id: uuid.UUID) -> Paciente:
    """
    Soft Delete de un paciente: cambia su estado a "dado_de_alta" y registra la fecha de alta.
    """
    paciente = await obtener_paciente(db, paciente_id)

    if paciente.estado == EstadoPaciente.dado_de_alta:
        # Evita pisar la fecha_alta original si lo llaman dos veces.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El paciente ya fue dado de alta.",
        )

    paciente.estado = EstadoPaciente.dado_de_alta
    paciente.fecha_alta = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(paciente)
    return paciente

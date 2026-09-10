import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinico import Alerta, Evento, TipoSignoVital
from app.models.enums import EstadoAlerta, NivelSeveridad, TipoEvento
from app.models.pacientes import DigitalTwin

# Ventana de "alarm fatigue": tras resolver una alerta, le damos este
# margen (en segundos) para que el valor asiente antes de considerar
# que una medición fuera de rango es un problema nuevo.
# Debe ser mayor a la duración total de la simulación de estabilización
# automática (ver PASOS_ESTABILIZACION / INTERVALO_ESTABILIZACION_SEG
# en temporal/activities.py) para que esta ventana la cubra por completo.
VENTANA_SUPRESION_SEG = 110

def evaluar_severidad(valor: Decimal, tipo_signo: TipoSignoVital) -> NivelSeveridad:
    """
    Compara un valor medido contra los 4 umbrales del tipo de signo vital
    y devuelve el nivel de severidad correspondiente.
    """
    if tipo_signo.rango_normal_min <= valor <= tipo_signo.rango_normal_max:
        return NivelSeveridad.normal

    if tipo_signo.rango_critico_min <= valor < tipo_signo.rango_normal_min:
        return NivelSeveridad.precaucion

    if tipo_signo.rango_normal_max < valor <= tipo_signo.rango_critico_max:
        return NivelSeveridad.precaucion

    return NivelSeveridad.critica


async def _hay_alerta_resuelta_reciente(
    db: AsyncSession, paciente_id: uuid.UUID, tipo_signo_id: uuid.UUID
) -> bool:
    """
    Busca la última Alerta resuelta para este paciente + tipo de signo y
    devuelve True si cayó dentro de la ventana de supresión.
    """
    ultima_resuelta = await db.scalar(
        select(Alerta)
        .where(
            Alerta.paciente_id == paciente_id,
            Alerta.tipo_signo_id == tipo_signo_id,
            Alerta.estado == EstadoAlerta.resuelta,
        )
        .order_by(Alerta.resuelta_en.desc())
        .limit(1)
    )

    if ultima_resuelta is None or ultima_resuelta.resuelta_en is None:
        return False

    return (datetime.now(timezone.utc) - ultima_resuelta.resuelta_en) < timedelta(
        seconds=VENTANA_SUPRESION_SEG
    )


async def procesar_nueva_medicion(
    db: AsyncSession,
    paciente_id: uuid.UUID,
    tipo_signo_id: uuid.UUID,
    valor: Decimal,
) -> dict:
    """
    Se llama después de que la medición YA fue agregada a la sesión
    en `signos_vitales` — ese registro es responsabilidad del servicio de
    signos vitales, no de este módulo.

    Calcula la severidad con evaluar_severidad(), deja SIEMPRE un Evento
    Si la severidad no es "normal", crea una Alerta nueva o
    actualiza la que ya esté activa para ese paciente + tipo de
    signo. Actualiza digital_twins.severidad_actual SOLO si cambió.

    No hace commit: eso queda a cargo de quien llama, para que la
    medición, el evento, la alerta y el digital twin se guarden como una
    sola transacción atómica.
    """
    tipo_signo = await db.get(TipoSignoVital, tipo_signo_id)
    if tipo_signo is None:
        raise ValueError(f"No existe un tipo de signo vital con id {tipo_signo_id}")

    severidad = evaluar_severidad(valor, tipo_signo)

    # Evento, siempre se registra
    evento = Evento(
        paciente_id=paciente_id,
        tipo=TipoEvento.registro_signo,
        descripcion=f"{tipo_signo.nombre}: {valor} {tipo_signo.unidad}",
        severidad=severidad,
    )
    db.add(evento)

    alerta = None
    alerta_es_nueva = False

    # Alerta: solo si la severidad no es normal
    if severidad != NivelSeveridad.normal:
        alerta_existente = await db.scalar(
            select(Alerta).where(
                Alerta.paciente_id == paciente_id,
                Alerta.tipo_signo_id == tipo_signo_id,
                Alerta.estado == EstadoAlerta.activa,
            )
        )

        if alerta_existente is not None:
            alerta_existente.severidad = severidad
            alerta_existente.valor_detectado = valor
            alerta = alerta_existente
            db.add(Evento(
                paciente_id=paciente_id,
                tipo=TipoEvento.alerta_actualizada,
                descripcion=f"Alerta actualizada a {severidad.value}",
                severidad=severidad,
            ))
        elif await _hay_alerta_resuelta_reciente(db, paciente_id, tipo_signo_id):
            # Ventana de supresión activa: no generamos una alerta nueva,
            # pero dejamos rastro en el historial de que el paciente
            # sigue fuera de rango mientras se estabiliza.
            db.add(
                Evento(
                    paciente_id=paciente_id,
                    tipo=TipoEvento.alerta_actualizada,
                    descripcion=(
                        f"{tipo_signo.nombre} en {severidad.value} dentro de la "
                        "ventana de supresión post-intervención; no se generó "
                        "una alerta nueva."
                    ),
                    severidad=severidad,
                )
            )
        else:
            alerta = Alerta(
                paciente_id=paciente_id,
                tipo_signo_id=tipo_signo_id,
                severidad=severidad,
                valor_detectado=valor,
                estado=EstadoAlerta.activa,
            )
            db.add(alerta)
            alerta_es_nueva = True
            db.add(Evento(
                paciente_id=paciente_id,
                tipo=TipoEvento.alerta_generada,
                descripcion=f"Alerta generada: {severidad.value}",
                severidad=severidad,
            ))

    # Digital Twin: actualizar severidad_actual solo si cambió
    digital_twin = await db.scalar(
        select(DigitalTwin).where(DigitalTwin.paciente_id == paciente_id)
    )
    if digital_twin is not None and digital_twin.severidad_actual != severidad:
        digital_twin.severidad_actual = severidad

    await db.flush()

    return {
        "severidad": severidad,
        "evento": evento,
        "alerta": alerta,
        "alerta_es_nueva": alerta_es_nueva,
    }

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinico import Alerta, Evento, SignoVital, TipoSignoVital
from app.models.enums import EstadoAlerta, NivelSeveridad, TipoEvento
from app.models.pacientes import DigitalTwin

# Ventana de "alarm fatigue": tras resolver una alerta, le damos este
# margen (en segundos) para que el valor asiente antes de considerar
# que una medición fuera de rango es un problema nuevo.
# Debe ser mayor a la duración total de la simulación de estabilización
# automática (ver PASOS_ESTABILIZACION / INTERVALO_ESTABILIZACION_SEG
# en temporal/activities.py) para que esta ventana la cubra por completo.
VENTANA_SUPRESION_SEG = 110

# Orden de gravedad para comparar severidades -- mayor índice = más grave.
_ORDEN_SEVERIDAD = [NivelSeveridad.normal, NivelSeveridad.precaucion, NivelSeveridad.critica]


def _severidad_maxima(a: NivelSeveridad, b: NivelSeveridad) -> NivelSeveridad:
    """Compara dos severidades y devuelve la más grave de las dos."""
    return max((a, b), key=lambda s: _ORDEN_SEVERIDAD.index(s))


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
        Alerta.resuelta_en.isnot(None),  # una "resuelta" sin fecha es un dato corrupto, no cuenta
    )
    .order_by(Alerta.resuelta_en.desc().nullslast())  # defensa extra por si vuelve a colarse un NULL
    .limit(1)
)

    if ultima_resuelta is None or ultima_resuelta.resuelta_en is None:
        return False

    return (datetime.now(timezone.utc) - ultima_resuelta.resuelta_en) < timedelta(
        seconds=VENTANA_SUPRESION_SEG
    )


async def _calcular_severidad_actual_paciente(
    db: AsyncSession, paciente_id: uuid.UUID
) -> NivelSeveridad:
    """
    Severidad real del paciente en este instante: para CADA tipo de
    signo vital, evalúa la severidad de su medición más reciente, y
    devuelve la más grave entre todas.

    A diferencia de mirar la tabla de Alertas, esto no depende de si
    existe o no una Alerta activa (que puede estar suprimida durante la
    ventana post-intervención, o ya resuelta aunque el valor real
    todavía no volvió a la normalidad) -- siempre refleja el estado
    físico actual de cada signo, sin que la medición de uno pueda pisar
    el estado de otro.
    """
    ultima_medicion_por_tipo = (
        select(
            SignoVital.tipo_signo_id,
            func.max(SignoVital.medido_en).label("medido_en"),
        )
        .where(SignoVital.paciente_id == paciente_id)
        .group_by(SignoVital.tipo_signo_id)
        .subquery()
    )

    resultado = await db.execute(
        select(SignoVital, TipoSignoVital)
        .join(TipoSignoVital, SignoVital.tipo_signo_id == TipoSignoVital.id)
        .join(
            ultima_medicion_por_tipo,
            (SignoVital.tipo_signo_id == ultima_medicion_por_tipo.c.tipo_signo_id)
            & (SignoVital.medido_en == ultima_medicion_por_tipo.c.medido_en),
        )
        .where(SignoVital.paciente_id == paciente_id)
    )

    peor = NivelSeveridad.normal
    for signo, tipo in resultado.all():
        peor = _severidad_maxima(peor, evaluar_severidad(signo.valor, tipo))
    return peor


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
    signo. Actualiza digital_twins.severidad_actual con la más grave
    entre: (a) todas las alertas activas del paciente, y (b) la
    severidad de ESTA medición puntual -- (b) es necesario porque, dentro
    de la ventana de supresión post-intervención, una medición fuera de
    rango no genera ni actualiza ninguna Alerta, pero el twin igual tiene
    que reflejar que el signo real todavía no volvió a la normalidad.

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
            severidad_cambio = alerta_existente.severidad != severidad
            alerta_existente.severidad = severidad
            alerta_existente.valor_detectado = valor
            alerta = alerta_existente
            if severidad_cambio:
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
                        f"{tipo_signo.nombre} persiste en {severidad.value},  en seguimiento post-intervención; sin alerta nueva."
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

    # Flush explícito: nos aseguramos de que la Alerta recién creada o
    # actualizada arriba ya esté visible para el SELECT de
    # _calcular_severidad_maxima_activa, sin depender del autoflush
    # implícito de la sesión.
    await db.flush()

    # Digital Twin: severidad_actual = la más grave entre las alertas
    # ACTIVAS del paciente y la severidad de esta medición puntual.
    digital_twin = await db.scalar(
        select(DigitalTwin)
        .where(DigitalTwin.paciente_id == paciente_id)
        .with_for_update()
    )
    if digital_twin is not None:
        severidad_alertas_activas = await _calcular_severidad_actual_paciente(
            db, paciente_id
        )
        nueva_severidad_twin = _severidad_maxima(severidad_alertas_activas, severidad)
        if digital_twin.severidad_actual != nueva_severidad_twin:
            digital_twin.severidad_actual = nueva_severidad_twin

    await db.flush()

    return {
        "severidad": severidad,
        "evento": evento,
        "alerta": alerta,
        "alerta_es_nueva": alerta_es_nueva,
    }

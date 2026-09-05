import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinico import Alerta, Evento, TipoSignoVital
from app.models.enums import EstadoAlerta, NivelSeveridad, TipoEvento
from app.models.pacientes import DigitalTwin


def evaluar_severidad(valor: Decimal, tipo_signo: TipoSignoVital) -> NivelSeveridad:
    """
    Compara un valor medido contra los 4 umbrales del tipo de signo vital
    y devuelve el nivel de severidad correspondiente.

    Bandas simétricas: tanto muy bajo como muy alto es peligroso. Los
    límites normal_min/normal_max son inclusive para "normal". Los
    límites crítico_min/crítico_max son inclusive para "precaución"
    (tocar justo el límite crítico todavía es precaución; "crítica" es
    estrictamente más allá de ese límite).
    """
    if tipo_signo.rango_normal_min <= valor <= tipo_signo.rango_normal_max:
        return NivelSeveridad.normal

    if tipo_signo.rango_critico_min <= valor < tipo_signo.rango_normal_min:
        return NivelSeveridad.precaucion

    if tipo_signo.rango_normal_max < valor <= tipo_signo.rango_critico_max:
        return NivelSeveridad.precaucion

    return NivelSeveridad.critica


# Estados de Alerta que consideramos "en curso" para efectos del motor de
# detección: mientras la alerta esté en cualquiera de estos, nos importa
# seguir reflejando ahí la severidad más reciente y seguir señalizando su
# AlertaWorkflow. Solo "resuelta" (via Intervencion) saca a una alerta de
# este radar -- a partir de ahí, una medición fuera de rango para el mismo
# paciente + tipo de signo abre una Alerta NUEVA.
ESTADOS_ALERTA_EN_CURSO = (EstadoAlerta.activa, EstadoAlerta.en_atencion)


async def procesar_nueva_medicion(
    db: AsyncSession,
    paciente_id: uuid.UUID,
    tipo_signo_id: uuid.UUID,
    valor: Decimal,
) -> dict:
    """
    Punto de entrada del motor de detección. Se llama después de que la
    medición YA fue agregada a la sesión (no comiteada todavía) en
    `signos_vitales` — ese registro es responsabilidad del servicio de
    signos vitales, no de este módulo.

    Maneja las CONSECUENCIAS de la medición:
      1. Calcula la severidad con evaluar_severidad().
      2. Deja SIEMPRE un Evento (bitácora).
      3. Busca si hay una Alerta en curso para ese paciente + tipo de
         signo (ESTADOS_ALERTA_EN_CURSO), sin importar si la medición
         actual dio normal o no:
           - Si la severidad NO es normal: crea una Alerta nueva, o
             actualiza la severidad/valor de la que ya estaba en curso
             (evita duplicar alertas por la misma causa).
           - Si la severidad SÍ es normal y había una alerta en curso:
             NO tocamos Alerta.severidad acá. Eso es a propósito --
             decidir si el signo se "normalizó" de verdad (sostenido 10
             segundos seguidos, no solo esta medición puntual) es
             responsabilidad del AlertaWorkflow de Temporal, que
             persiste el cambio via la Activity marcar_alerta_normalizada
             cuando corresponde. Este módulo solo devuelve la alerta
             para que el caller la señalice.
           - Si la severidad es normal y NO había alerta en curso, no
             hacemos nada (nunca hubo nada que corregir).
      4. Actualiza digital_twins.severidad_actual SOLO si cambió (este
         campo sí refleja la severidad instantánea de la última
         medición, a diferencia de Alerta.severidad).

    No hace commit: eso queda a cargo de quien llama, para que la
    medición, el evento, la alerta y el digital twin se guarden como una
    sola transacción atómica.

    Devuelve, además de lo de siempre, "alerta_es_nueva": bool -- el
    caller lo necesita para decidir si tiene que ARRANCAR un
    AlertaWorkflow nuevo o SEÑALIZAR uno que ya existe.
    """
    tipo_signo = await db.get(TipoSignoVital, tipo_signo_id)
    if tipo_signo is None:
        raise ValueError(f"No existe un tipo de signo vital con id {tipo_signo_id}")

    severidad = evaluar_severidad(valor, tipo_signo)

    # 1. Evento: bitácora, siempre se registra
    evento = Evento(
        paciente_id=paciente_id,
        tipo=TipoEvento.registro_signo,
        descripcion=f"{tipo_signo.nombre}: {valor} {tipo_signo.unidad}",
        severidad=severidad,
    )
    db.add(evento)

    alerta = None
    alerta_es_nueva = False

    # Buscamos la alerta en curso SIEMPRE (no solo cuando la severidad es
    # anormal) -- es la única forma de detectar que una alerta existente
    # necesita ser señalizada cuando el signo vuelve a rango normal.
    alerta_existente = await db.scalar(
        select(Alerta).where(
            Alerta.paciente_id == paciente_id,
            Alerta.tipo_signo_id == tipo_signo_id,
            Alerta.estado.in_(ESTADOS_ALERTA_EN_CURSO),
        )
    )

    if severidad != NivelSeveridad.normal:
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
        else:
            nueva_alerta_id = uuid.uuid4()
            alerta = Alerta(
                id=nueva_alerta_id,
                paciente_id=paciente_id,
                tipo_signo_id=tipo_signo_id,
                severidad=severidad,
                valor_detectado=valor,
                estado=EstadoAlerta.activa,
                # Usamos el mismo id como workflow_id de Temporal: es
                # único por diseño (uuid4) y nos ahorra generar y
                # trackear un identificador aparte.
                workflow_id_temporal=str(nueva_alerta_id),
            )
            db.add(alerta)
            alerta_es_nueva = True
            db.add(Evento(
                paciente_id=paciente_id,
                tipo=TipoEvento.alerta_generada,
                descripcion=f"Alerta generada: {severidad.value}",
                severidad=severidad,
            ))
    elif alerta_existente is not None:
        # Medición normal, pero hay una alerta en curso para esta misma
        # causa: la devolvemos tal cual (sin tocar su severidad) para
        # que el caller señalice al AlertaWorkflow y sea ÉL quien decida,
        # tras 10 segundos sostenidos, si corresponde normalizarla.
        alerta = alerta_existente

    # Digital Twin: actualizar severidad_actual solo si cambió
    digital_twin = await db.scalar(
        select(DigitalTwin).where(DigitalTwin.paciente_id == paciente_id)
    )
    if digital_twin is not None and digital_twin.severidad_actual != severidad:
        digital_twin.severidad_actual = severidad

    await db.flush()  # deja alerta.id / evento.id disponibles sin comitear

    return {
        "severidad": severidad,
        "evento": evento,
        "alerta": alerta,
        "alerta_es_nueva": alerta_es_nueva,
    }

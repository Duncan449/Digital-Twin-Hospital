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
      3. Si la severidad no es "normal", crea una Alerta nueva o
         actualiza la que ya esté activa para ese paciente + tipo de
         signo (evita duplicar alertas por la misma causa; la urgencia
         queda reflejada en Alerta.severidad, que puede ser "precaucion"
         o "critica").
      4. Actualiza digital_twins.severidad_actual SOLO si cambió.

    No hace commit: eso queda a cargo de quien llama, para que la
    medición, el evento, la alerta y el digital twin se guarden como una
    sola transacción atómica.
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

    # 2. Alerta: solo si la severidad no es normal
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
        else:
            alerta = Alerta(
                paciente_id=paciente_id,
                tipo_signo_id=tipo_signo_id,
                severidad=severidad,
                valor_detectado=valor,
                estado=EstadoAlerta.activa,
                # workflow_id_temporal se completa cuando integremos el
                # arranque del workflow de Temporal acá.
            )
            db.add(alerta)
            db.add(Evento(
                paciente_id=paciente_id,
                tipo=TipoEvento.alerta_generada,
                descripcion=f"Alerta generada: {severidad.value}",
                severidad=severidad,
            ))

    # 3. Digital Twin: actualizar severidad_actual solo si cambió
    digital_twin = await db.scalar(
        select(DigitalTwin).where(DigitalTwin.paciente_id == paciente_id)
    )
    if digital_twin is not None and digital_twin.severidad_actual != severidad:
        digital_twin.severidad_actual = severidad

    await db.flush()  # deja alerta.id / evento.id disponibles sin comitear

    return {"severidad": severidad, "evento": evento, "alerta": alerta}
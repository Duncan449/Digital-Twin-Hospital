import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import (
    EstadoAlerta,
    NivelSeveridad,
    OrigenMedicion,
    TipoEvento,
    pg_enum,
)


class TipoSignoVital(Base):
    '''Representa un tipo de signo vital que puede ser medido en un paciente, como la presión arterial, la frecuencia cardíaca, etc.
    Contiene información sobre el nombre del signo vital, la unidad de medida y los rangos'''
    __tablename__ = "tipos_signos_vitales"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    unidad: Mapped[str] = mapped_column(String(20), nullable=False)
    rango_normal_min: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    rango_normal_max: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    rango_critico_min: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    rango_critico_max: Mapped[Decimal] = mapped_column(Numeric(6, 2))


class SignoVital(Base):
    '''Representa una medición de un signo vital de un paciente en un momento específico.'''
    __tablename__ = "signos_vitales"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    paciente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pacientes.id", ondelete="CASCADE")
    )
    tipo_signo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tipos_signos_vitales.id")
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    origen: Mapped[OrigenMedicion] = mapped_column(
        pg_enum(OrigenMedicion, "origen_medicion"), default=OrigenMedicion.simulado
    )
    medido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    tipo_signo: Mapped["TipoSignoVital"] = relationship()


class Evento(Base):
    '''Representa un evento clínico relacionado con un paciente, como una intervención médica, un cambio en el estado de salud, etc.
    Contiene información sobre el tipo de evento, su descripción, la severidad y la fecha'''
    __tablename__ = "eventos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    paciente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pacientes.id", ondelete="CASCADE")
    )
    tipo: Mapped[TipoEvento] = mapped_column(
        pg_enum(TipoEvento, "tipo_evento"), nullable=False
    )
    descripcion: Mapped[str | None] = mapped_column(Text)
    severidad: Mapped[NivelSeveridad] = mapped_column(
        pg_enum(NivelSeveridad, "nivel_severidad"), default=NivelSeveridad.normal
    )
    ocurrido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Alerta(Base):
    '''Representa una alerta generada para un paciente, generalmente debido a una medición de signo vital fuera de los rangos normales.'''
    __tablename__ = "alertas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    paciente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pacientes.id", ondelete="CASCADE")
    )
    tipo_signo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tipos_signos_vitales.id", ondelete="SET NULL")
    )
    severidad: Mapped[NivelSeveridad] = mapped_column(
        pg_enum(NivelSeveridad, "nivel_severidad"), nullable=False
    )
    valor_detectado: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    estado: Mapped[EstadoAlerta] = mapped_column(
        pg_enum(EstadoAlerta, "estado_alerta"), default=EstadoAlerta.activa
    )
    # Correlación con Temporal: acá guardamos el mismo UUID (como string)
    # que usamos como workflow_id al arrancar el workflow de la alerta.
    workflow_id_temporal: Mapped[str | None] = mapped_column(String(255), unique=True)
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resuelta_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    intervenciones: Mapped[list["Intervencion"]] = relationship(back_populates="alerta")


class Intervencion(Base):
    '''Representa una intervención realizada en respuesta a una alerta generada para un paciente.
    Contiene información sobre la acción tomada, el usuario que la realizó y las observaciones.'''
    __tablename__ = "intervenciones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    alerta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alertas.id", ondelete="CASCADE")
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    accion: Mapped[str] = mapped_column(String(150), nullable=False)
    observaciones: Mapped[str | None] = mapped_column(Text)
    iniciada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finalizada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    alerta: Mapped["Alerta"] = relationship(back_populates="intervenciones")

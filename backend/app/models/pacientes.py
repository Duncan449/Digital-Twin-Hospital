import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import EstadoPaciente, NivelSeveridad, pg_enum


class Paciente(Base):
    '''Representa un paciente en el sistema.
    Contiene información personal y médica del paciente, así como su estado actual en el hospital.'''
    __tablename__ = "pacientes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    documento: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    genero: Mapped[str | None] = mapped_column(String(20))
    sala: Mapped[str | None] = mapped_column(String(50))
    cama: Mapped[str | None] = mapped_column(String(20))
    estado: Mapped[EstadoPaciente] = mapped_column(
        pg_enum(EstadoPaciente, "estado_paciente"), default=EstadoPaciente.internado
    )
    fecha_ingreso: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fecha_alta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # uselist=False porque es 1:1 -- paciente.digital_twin devuelve un solo objeto, no una lista
    digital_twin: Mapped["DigitalTwin"] = relationship(
        back_populates="paciente", uselist=False
    )


class DigitalTwin(Base):
    '''Representa el "gemelo digital" de un paciente, que es una representación virtual del estado de salud del paciente.
    Contiene información sobre la severidad actual del paciente y la fecha de la última actualización.'''
    __tablename__ = "digital_twins"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    paciente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pacientes.id", ondelete="CASCADE"), unique=True
    )
    severidad_actual: Mapped[NivelSeveridad] = mapped_column(
        pg_enum(NivelSeveridad, "nivel_severidad"), default=NivelSeveridad.normal
    )
    ultima_actualizacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    paciente: Mapped["Paciente"] = relationship(back_populates="digital_twin")

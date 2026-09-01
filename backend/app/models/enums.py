import enum

from sqlalchemy import Enum as PgEnum


class EstadoPaciente(str, enum.Enum):   
    internado = "internado"
    dado_de_alta = "dado_de_alta"


class NivelSeveridad(str, enum.Enum):
    normal = "normal"
    precaucion = "precaucion"
    critica = "critica"


class EstadoAlerta(str, enum.Enum):
    activa = "activa"
    en_atencion = "en_atencion"
    resuelta = "resuelta"


class OrigenMedicion(str, enum.Enum):
    simulado = "simulado"
    joystick = "joystick"
    manual = "manual"


class TipoEvento(str, enum.Enum):
    registro_signo = "registro_signo"
    alerta_generada = "alerta_generada"
    alerta_actualizada = "alerta_actualizada"
    intervencion_registrada = "intervencion_registrada"
    paciente_creado = "paciente_creado"
    paciente_actualizado = "paciente_actualizado"


def pg_enum(python_enum: type[enum.Enum], nombre_pg: str) -> PgEnum:
    """
    Mapea un Enum de Python a un tipo ENUM que YA existe en Postgres
    (los creamos a mano en schema.sql, ej: CREATE TYPE estado_paciente ...).

    create_type=False es la parte importante: le dice a SQLAlchemy (y a
    Alembic cuando comparemos modelos contra la base) que NO intente crear
    el tipo de nuevo, porque ya existe. Sin esto, Alembic autogenerate
    marcaría un cambio falso cada vez que corramos --autogenerate.
    """
    return PgEnum(python_enum, name=nombre_pg, create_type=False)

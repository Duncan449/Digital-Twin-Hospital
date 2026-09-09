// Espeja backend/app/models/enums.py
// Union types en vez de "enum" de TS: son más simples y se comparan
// directo con === contra el string que manda la API (no hace falta
// mapear Enum.Valor -> string en cada lugar donde se usan).

export type EstadoPaciente = "internado" | "dado_de_alta";

export type NivelSeveridad = "normal" | "precaucion" | "critica";

export type EstadoAlerta = "activa" | "en_atencion" | "resuelta";

export type OrigenMedicion = "simulado" | "joystick" | "manual";

export type TipoEvento =
  | "registro_signo"
  | "alerta_generada"
  | "alerta_actualizada"
  | "intervencion_registrada"
  | "paciente_creado"
  | "paciente_actualizado";

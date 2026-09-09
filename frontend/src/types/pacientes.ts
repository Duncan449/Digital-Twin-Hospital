// Espeja backend/app/schemas/pacientes.py (PacienteRespuesta) y
// backend/app/models/pacientes.py (DigitalTwin).
//
// A propósito NO incluyo PacienteCrear/PacienteActualizar todavía: el
// frontend por ahora solo LEE datos (dashboard + vista de paciente).
// Cuando armen el formulario de alta de paciente, se agregan acá.

import type { EstadoPaciente, NivelSeveridad } from "./enums";

export interface Paciente {
  id: string; // UUID viaja como string en JSON, no hace falta un tipo especial
  nombre: string;
  apellido: string;
  documento: string;
  fecha_nacimiento: string; // formato "YYYY-MM-DD" (date de Python -> string)
  estado: EstadoPaciente;
  sala: string | null;
  cama: string | null;
  fecha_ingreso: string; // ISO datetime string
  // No es opcional: todo paciente se crea con su digital twin en la misma
  // transacción atómica (ver crear_paciente en el backend), así que
  // PacienteRespuesta SIEMPRE lo trae anidado, nunca en null.
  digital_twin: DigitalTwin;
}

export interface DigitalTwin {
  id: string;
  paciente_id: string;
  severidad_actual: NivelSeveridad;
  ultima_actualizacion: string;
  creado_en: string;
}

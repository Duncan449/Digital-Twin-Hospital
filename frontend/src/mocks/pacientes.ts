// Datos de prueba fijos, tipados contra types/pacientes.ts.
// A propósito hay pacientes con distinta severidad y en distinta sala:
// así el Dashboard se puede probar con casos reales (crítico, precaución,
// normal) sin depender de que el simulador esté corriendo.
//
// El digital_twin va ANIDADO dentro de cada paciente, no en un array
// aparte: así el mock refleja exactamente lo que devuelve GET /pacientes
// en el backend real (PacienteRespuesta ya trae digital_twin adentro).

import type { Paciente } from "../types/pacientes";

export const pacientesMock: Paciente[] = [
  {
    id: "a1b2c3d4-0000-0000-0000-000000000001",
    nombre: "Marta",
    apellido: "Gómez",
    documento: "30111222",
    fecha_nacimiento: "1958-04-12",
    estado: "internado",
    sala: "Terapia Intensiva",
    cama: "3",
    fecha_ingreso: "2026-09-01T14:20:00Z",
    digital_twin: {
      id: "b1b2c3d4-0000-0000-0000-000000000001",
      paciente_id: "a1b2c3d4-0000-0000-0000-000000000001",
      severidad_actual: "critica",
      ultima_actualizacion: "2026-09-08T15:02:00Z",
      creado_en: "2026-09-01T14:20:00Z",
    },
  },
  {
    id: "a1b2c3d4-0000-0000-0000-000000000002",
    nombre: "Julián",
    apellido: "Fernández",
    documento: "28555444",
    fecha_nacimiento: "1975-11-02",
    estado: "internado",
    sala: "Clínica Médica",
    cama: "12",
    fecha_ingreso: "2026-09-03T09:15:00Z",
    digital_twin: {
      id: "b1b2c3d4-0000-0000-0000-000000000002",
      paciente_id: "a1b2c3d4-0000-0000-0000-000000000002",
      severidad_actual: "precaucion",
      ultima_actualizacion: "2026-09-08T14:47:00Z",
      creado_en: "2026-09-03T09:15:00Z",
    },
  },
  {
    id: "a1b2c3d4-0000-0000-0000-000000000003",
    nombre: "Rocío",
    apellido: "Benítez",
    documento: "40222333",
    fecha_nacimiento: "1990-07-23",
    estado: "internado",
    sala: "Clínica Médica",
    cama: "14",
    fecha_ingreso: "2026-09-06T18:40:00Z",
    digital_twin: {
      id: "b1b2c3d4-0000-0000-0000-000000000003",
      paciente_id: "a1b2c3d4-0000-0000-0000-000000000003",
      severidad_actual: "normal",
      ultima_actualizacion: "2026-09-08T13:10:00Z",
      creado_en: "2026-09-06T18:40:00Z",
    },
  },
  {
    id: "a1b2c3d4-0000-0000-0000-000000000004",
    nombre: "Osvaldo",
    apellido: "Ledesma",
    documento: "15999888",
    fecha_nacimiento: "1949-01-30",
    estado: "dado_de_alta",
    sala: null,
    cama: null,
    fecha_ingreso: "2026-08-20T10:00:00Z",
    digital_twin: {
      id: "b1b2c3d4-0000-0000-0000-000000000004",
      paciente_id: "a1b2c3d4-0000-0000-0000-000000000004",
      severidad_actual: "normal",
      ultima_actualizacion: "2026-08-25T09:00:00Z",
      creado_en: "2026-08-20T10:00:00Z",
    },
  },
];

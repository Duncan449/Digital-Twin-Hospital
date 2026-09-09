// Igual que mocks/pacientes.ts: datos fijos tipados contra types/clinico.ts.
// Los ids de tipo_signo acá abajo son inventados pero se reutilizan como
// constantes (TIPO_FC, TIPO_SAT, etc.) para no repetir el mismo UUID a mano
// en cada medición — mismo motivo por el que en el backend fk apuntan a
// tipos_signos_vitales en vez de duplicar nombre/unidad en cada fila.
//
// Los valores numéricos van entre comillas (ej. "60.00") porque así es
// como los devuelve realmente la API -- confirmado en Swagger. Si acá
// pusiéramos 60 (number) en vez de "60.00" (string), TypeScript tiraría
// error de tipos apenas guardás el archivo.

import type {
  TipoSignoVital,
  SignoVital,
  Alerta,
  Evento,
} from "../types/clinico";

// Rangos calcados de los 6 tipos ya seedeados en Neon (mismos valores
// clínicos estándar). Si en algún momento cambian los rangos reales
// en la base, actualizar acá también para que el mock no mienta.
const TIPO_FRECUENCIA_RESPIRATORIA = "c1000000-0000-0000-0000-000000000001";
const TIPO_PRESION_SISTOLICA = "c1000000-0000-0000-0000-000000000002";
const TIPO_TEMPERATURA_CORPORAL = "c1000000-0000-0000-0000-000000000003";
const TIPO_SATURACION_OXIGENO = "c1000000-0000-0000-0000-000000000004";
const TIPO_FRECUENCIA_CARDIACA = "c1000000-0000-0000-0000-000000000005";
const TIPO_PRESION_DIASTOLICA = "c1000000-0000-0000-0000-000000000006";

export const tiposSignosVitalesMock: TipoSignoVital[] = [
  {
    id: TIPO_FRECUENCIA_RESPIRATORIA,
    nombre: "Frecuencia respiratoria",
    unidad: "rpm",
    rango_normal_min: "12.00",
    rango_normal_max: "20.00",
    rango_critico_min: "8.00",
    rango_critico_max: "30.00",
  },
  {
    id: TIPO_PRESION_SISTOLICA,
    nombre: "Presión sistólica",
    unidad: "mmHg",
    rango_normal_min: "90.00",
    rango_normal_max: "120.00",
    rango_critico_min: "70.00",
    rango_critico_max: "180.00",
  },
  {
    id: TIPO_TEMPERATURA_CORPORAL,
    nombre: "Temperatura corporal",
    unidad: "°C",
    rango_normal_min: "36.00",
    rango_normal_max: "37.50",
    rango_critico_min: "34.00",
    rango_critico_max: "40.00",
  },
  {
    id: TIPO_SATURACION_OXIGENO,
    nombre: "Saturación de oxígeno",
    unidad: "%",
    rango_normal_min: "95.00",
    rango_normal_max: "100.00",
    rango_critico_min: "85.00",
    rango_critico_max: "100.00",
  },
  {
    id: TIPO_FRECUENCIA_CARDIACA,
    nombre: "Frecuencia cardíaca",
    unidad: "lpm",
    rango_normal_min: "60.00",
    rango_normal_max: "100.00",
    rango_critico_min: "40.00",
    rango_critico_max: "150.00",
  },
  {
    id: TIPO_PRESION_DIASTOLICA,
    nombre: "Presión diastólica",
    unidad: "mmHg",
    rango_normal_min: "60.00",
    rango_normal_max: "80.00",
    rango_critico_min: "40.00",
    rango_critico_max: "110.00",
  },
];

// Historial de Marta Gómez (paciente crítico en mocks/pacientes.ts):
// frecuencia cardíaca subiendo y saturación bajando con el tiempo, para
// que el gráfico de Recharts tenga una tendencia real que mostrar, no
// puntos sueltos sin relación entre sí.
const PACIENTE_MARTA = "a1b2c3d4-0000-0000-0000-000000000001";

export const signosVitalesMock: SignoVital[] = [
  {
    id: "d1000000-0000-0000-0000-000000000001",
    paciente_id: PACIENTE_MARTA,
    tipo_signo_id: TIPO_FRECUENCIA_CARDIACA,
    valor: "88.00",
    origen: "simulado",
    medido_en: "2026-09-08T13:00:00Z",
  },
  {
    id: "d1000000-0000-0000-0000-000000000002",
    paciente_id: PACIENTE_MARTA,
    tipo_signo_id: TIPO_FRECUENCIA_CARDIACA,
    valor: "102.00",
    origen: "simulado",
    medido_en: "2026-09-08T13:30:00Z",
  },
  {
    id: "d1000000-0000-0000-0000-000000000003",
    paciente_id: PACIENTE_MARTA,
    tipo_signo_id: TIPO_FRECUENCIA_CARDIACA,
    valor: "118.00",
    origen: "simulado",
    medido_en: "2026-09-08T14:15:00Z",
  },
  {
    id: "d1000000-0000-0000-0000-000000000004",
    paciente_id: PACIENTE_MARTA,
    tipo_signo_id: TIPO_FRECUENCIA_CARDIACA,
    valor: "131.00",
    origen: "simulado",
    medido_en: "2026-09-08T15:02:00Z",
  },
  {
    id: "d1000000-0000-0000-0000-000000000005",
    paciente_id: PACIENTE_MARTA,
    tipo_signo_id: TIPO_SATURACION_OXIGENO,
    valor: "96.00",
    origen: "simulado",
    medido_en: "2026-09-08T13:00:00Z",
  },
  {
    id: "d1000000-0000-0000-0000-000000000006",
    paciente_id: PACIENTE_MARTA,
    tipo_signo_id: TIPO_SATURACION_OXIGENO,
    valor: "91.00",
    origen: "simulado",
    medido_en: "2026-09-08T14:15:00Z",
  },
  {
    id: "d1000000-0000-0000-0000-000000000007",
    paciente_id: PACIENTE_MARTA,
    tipo_signo_id: TIPO_SATURACION_OXIGENO,
    valor: "87.00",
    origen: "simulado",
    medido_en: "2026-09-08T15:02:00Z",
  },
];

// Una alerta activa para Marta, coherente con su última medición de
// frecuencia cardíaca (131 lpm, fuera del rango crítico de 150 todavía
// no, pero ya fuera del normal). workflow_id_temporal en null a propósito:
// así el mock también sirve para probar en el frontend el caso de
// "Temporal no pudo iniciar el workflow" (degradación graceful), que es
// un estado real que el backend contempla.
export const alertasMock: Alerta[] = [
  {
    id: "e1000000-0000-0000-0000-000000000001",
    paciente_id: PACIENTE_MARTA,
    tipo_signo_id: TIPO_FRECUENCIA_CARDIACA,
    severidad: "critica",
    valor_detectado: "131.00",
    estado: "activa",
    workflow_id_temporal: null,
    creada_en: "2026-09-08T15:02:00Z",
    resuelta_en: null,
  },
];

// Historial de eventos de Marta: un registro normal al principio, y la
// secuencia de alerta generada -> actualizada a medida que empeoró.
export const eventosMock: Evento[] = [
  {
    id: "f1000000-0000-0000-0000-000000000001",
    paciente_id: PACIENTE_MARTA,
    tipo: "registro_signo",
    descripcion: "Frecuencia cardíaca: 88 lpm",
    severidad: "normal",
    ocurrido_en: "2026-09-08T13:00:00Z",
  },
  {
    id: "f1000000-0000-0000-0000-000000000002",
    paciente_id: PACIENTE_MARTA,
    tipo: "alerta_generada",
    descripcion: "Alerta generada: precaucion",
    severidad: "precaucion",
    ocurrido_en: "2026-09-08T13:30:00Z",
  },
  {
    id: "f1000000-0000-0000-0000-000000000003",
    paciente_id: PACIENTE_MARTA,
    tipo: "alerta_actualizada",
    descripcion: "Alerta actualizada a critica",
    severidad: "critica",
    ocurrido_en: "2026-09-08T15:02:00Z",
  },
];

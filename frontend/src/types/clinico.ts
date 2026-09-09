// Espeja backend/app/schemas/{signos_vitales,tipos_signos_vitales,eventos,alertas}.py

import type {
  EstadoAlerta,
  NivelSeveridad,
  OrigenMedicion,
  TipoEvento,
} from "./enums";

// Los campos Decimal (valor, rangos) llegan como STRING desde la API,
// confirmado en Swagger contra un endpoint real (ej. "rango_normal_min":
// "60.00", con comillas). Por eso están tipados como string acá, no
// number. Donde se necesite operar con ellos (comparar, graficar en
// Recharts) hay que convertirlos con Number(...) en el componente/hook
// que los consuma -- no acá, para no perder precisión de más temprano
// de lo necesario.
export interface TipoSignoVital {
  id: string;
  nombre: string;
  unidad: string;
  rango_normal_min: string;
  rango_normal_max: string;
  rango_critico_min: string;
  rango_critico_max: string;
}

export interface SignoVital {
  id: string;
  paciente_id: string;
  tipo_signo_id: string;
  valor: string;
  origen: OrigenMedicion;
  medido_en: string; // ISO datetime string
}

export interface AlertaResumen {
  id: string;
  severidad: NivelSeveridad;
  estado: EstadoAlerta;
  valor_detectado: string;
}

// Espeja AlertaRespuesta (backend/app/schemas/alertas.py). A diferencia
// de AlertaResumen (que va anidada en la respuesta de una medición),
// esta es la versión completa que devuelven GET /alertas y afines —
// la vas a usar para listar alertas activas en el dashboard.
export interface Alerta {
  id: string;
  paciente_id: string;
  tipo_signo_id: string | null;
  severidad: NivelSeveridad;
  valor_detectado: string | null;
  estado: EstadoAlerta;
  workflow_id_temporal: string | null;
  creada_en: string;
  resuelta_en: string | null;
}

// Lo que devuelve POST /pacientes/{id}/signos-vitales:
// la medición guardada + el resultado del motor de detección.
export interface SignoVitalRegistradoRespuesta {
  signo_vital: SignoVital;
  severidad_calculada: NivelSeveridad;
  alerta: AlertaResumen | null;
}

export interface Evento {
  id: string;
  paciente_id: string;
  tipo: TipoEvento;
  descripcion: string | null;
  severidad: NivelSeveridad;
  ocurrido_en: string;
}

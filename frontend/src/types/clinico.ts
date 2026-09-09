// Espeja backend/app/schemas/{signos_vitales,tipos_signos_vitales,eventos}.py

import type {
  EstadoAlerta,
  NivelSeveridad,
  OrigenMedicion,
  TipoEvento,
} from "./enums";

// OJO con los campos Decimal (valor, rango_normal_min, etc.): acá asumo
// que FastAPI los serializa como number. VERIFICAR en Swagger antes de
// dar por buena esta suposición (mismo error que ya tuvimos con el
// catálogo de tipos_signos_vitales: no asumir, confirmar). Si llegan
// como string (ej. "98.60"), cambiar `number` por `string` acá y
// convertir con Number(...) donde se grafique.

export interface TipoSignoVital {
  id: string;
  nombre: string;
  unidad: string;
  rango_normal_min: number;
  rango_normal_max: number;
  rango_critico_min: number;
  rango_critico_max: number;
}

export interface SignoVital {
  id: string;
  paciente_id: string;
  tipo_signo_id: string;
  valor: number;
  origen: OrigenMedicion;
  medido_en: string; // ISO datetime string
}

export interface AlertaResumen {
  id: string;
  severidad: NivelSeveridad;
  estado: EstadoAlerta;
  valor_detectado: number;
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
  valor_detectado: number | null;
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

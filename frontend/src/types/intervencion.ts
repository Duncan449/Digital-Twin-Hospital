// Espeja backend/app/schemas/intervenciones.py

export interface IntervencionCrear {
  accion: string;
  observaciones: string | null;
}

export interface IntervencionRespuesta {
  id: string;
  alerta_id: string;
  usuario_id: string | null;
  accion: string;
  observaciones: string | null;
  iniciada_en: string;
  finalizada_en: string | null;
}

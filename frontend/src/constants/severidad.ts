import type { NivelSeveridad } from "../types/enums";

// Ya NO duplicamos los hex acá: apuntamos a las mismas variables CSS que
// ya usa PatientCard.tsx (definidas en index.css). Antes este archivo
// tenía sus propios valores hardcodeados -- dos fuentes de verdad para
// el mismo dato. Con esto, cambiar un color de severidad se hace en un
// solo lugar (index.css) y se propaga solo a todo lo que lo consuma.
export const COLOR_SEVERIDAD: Record<NivelSeveridad, string> = {
  normal: "var(--color-normal)",
  precaucion: "var(--color-precaucion)",
  critica: "var(--color-critica)",
};

export const FONDO_SEVERIDAD: Record<NivelSeveridad, string> = {
  normal: "var(--tint-normal)",
  precaucion: "var(--tint-precaucion)",
  critica: "var(--tint-critica)",
};

export const BORDE_SEVERIDAD: Record<NivelSeveridad, string> = {
  normal: "var(--border-normal)",
  precaucion: "var(--border-precaucion)",
  critica: "var(--border-critica)",
};

// El glow de los paneles grandes es exclusivo de la vista del Digital
// Twin -- no existe todavía como variable en index.css. Si en algún
// momento se reutiliza en otro lugar (Dashboard, por ejemplo), ahí sí
// conviene subirlo a index.css junto a las demás.
export const GLOW_SEVERIDAD: Record<NivelSeveridad, string> = {
  normal: "rgba(16,185,129,.13)",
  precaucion: "rgba(245,158,11,.15)",
  critica: "rgba(239,68,68,.25)",
};

export const ETIQUETA_SEVERIDAD: Record<NivelSeveridad, string> = {
  normal: "Estable",
  precaucion: "Precaución",
  critica: "Crítico",
};

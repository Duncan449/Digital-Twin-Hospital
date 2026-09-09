import type { NivelSeveridad } from "../types/enums";
import {
  COLOR_SEVERIDAD,
  FONDO_SEVERIDAD,
  BORDE_SEVERIDAD,
  ETIQUETA_SEVERIDAD,
} from "../constants/severidad";

interface SeveridadBadgeProps {
  severidad: NivelSeveridad;
}

function SeveridadBadge({ severidad }: SeveridadBadgeProps) {
  return (
    <span
      style={{
        padding: "6px 13px",
        borderRadius: 8,
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.14em",
        color: COLOR_SEVERIDAD[severidad],
        background: FONDO_SEVERIDAD[severidad],
        border: `1px solid ${BORDE_SEVERIDAD[severidad]}`,
        animation:
          severidad === "critica"
            ? "critblink 1.1s ease-in-out infinite"
            : "none",
      }}
    >
      {ETIQUETA_SEVERIDAD[severidad].toUpperCase()}
    </span>
  );
}

export default SeveridadBadge;

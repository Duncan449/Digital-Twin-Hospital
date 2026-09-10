// frontend/src/components/VitalSignCard.tsx
import type { SignoVital, TipoSignoVital } from "../types/clinico";
import { calcularSeveridadSigno } from "../utils/severidadSigno";
import { COLOR_SEVERIDAD, BORDE_SEVERIDAD } from "../constants/severidad";

interface VitalSignCardProps {
  tipo: TipoSignoVital;
  ultimaMedicion: SignoVital | undefined;
}

function VitalSignCard({ tipo, ultimaMedicion }: VitalSignCardProps) {
  if (ultimaMedicion === undefined) {
    return (
      <div
        style={{
          padding: 18,
          borderRadius: 14,
          background: "#070E1A",
          border: "1px solid #16223A",
        }}
      >
        <div
          style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 10,
            letterSpacing: "0.16em",
            color: "#6B819F",
          }}
        >
          {tipo.nombre.toUpperCase()}
        </div>
        <div style={{ marginTop: 8, fontSize: 13, color: "#43587A" }}>
          Sin mediciones todavía
        </div>
      </div>
    );
  }

  // valor y los rango_* llegan como string (Decimal de Postgres vía
  // FastAPI) -- convertimos acá, en el borde del componente, para que
  // el resto de las cuentas trabaje con number sin sorpresas.
  const valor = Number(ultimaMedicion.valor);
  const rangoNormalMin = Number(tipo.rango_normal_min);
  const rangoNormalMax = Number(tipo.rango_normal_max);
  const rangoCriticoMin = Number(tipo.rango_critico_min);
  const rangoCriticoMax = Number(tipo.rango_critico_max);

  const severidad = calcularSeveridadSigno(valor, tipo);
  const color = COLOR_SEVERIDAD[severidad];

  // Porcentaje relativo al rango CRÍTICO completo (no al normal): así un
  // valor apenas fuera de rango normal no llena la barra entera de golpe.
  const porcentaje = Math.min(
    100,
    Math.max(
      0,
      ((valor - rangoCriticoMin) / (rangoCriticoMax - rangoCriticoMin)) * 100,
    ),
  );

  const etiquetaFlag =
    severidad === "normal"
      ? "NORMAL"
      : severidad === "precaucion"
        ? "PRECAUCIÓN"
        : "CRÍTICO";

  return (
    <div
      style={{
        padding: 18,
        borderRadius: 14,
        background: "#070E1A",
        border: `1px solid ${BORDE_SEVERIDAD[severidad]}`,
      }}
    >
      <div
        style={{
          fontFamily: "'IBM Plex Mono', monospace",
          fontSize: 10,
          letterSpacing: "0.16em",
          color: "#6B819F",
        }}
      >
        {tipo.nombre.toUpperCase()}
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: 7,
          marginTop: 8,
        }}
      >
        <span
          style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 44,
            fontWeight: 600,
            lineHeight: 0.95,
            color,
            animation:
              severidad === "critica"
                ? "critblink 1.1s ease-in-out infinite"
                : "none",
          }}
        >
          {valor}
        </span>
        <span
          style={{
            fontFamily: "'IBM Plex Mono', monospace",
            fontSize: 13,
            color: "#6B819F",
          }}
        >
          {tipo.unidad}
        </span>
      </div>
      <div
        style={{
          marginTop: 12,
          height: 5,
          borderRadius: 4,
          background: "#131E33",
          overflow: "hidden",
        }}
      >
        <div
          style={{ height: "100%", width: `${porcentaje}%`, background: color }}
        />
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginTop: 7,
          fontFamily: "'IBM Plex Mono', monospace",
          fontSize: 9.5,
          color: "#43587A",
        }}
      >
        <span>
          {rangoNormalMin}–{rangoNormalMax} {tipo.unidad}
        </span>
        <span style={{ color }}>{etiquetaFlag}</span>
      </div>
    </div>
  );
}

export default VitalSignCard;

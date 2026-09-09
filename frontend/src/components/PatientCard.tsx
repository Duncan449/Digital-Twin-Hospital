import { Link } from "react-router-dom";
import type { Paciente } from "../types/pacientes";
import type { NivelSeveridad } from "../types/enums";

interface PatientCardProps {
  paciente: Paciente;
}

type EstiloTarjeta = { color: string; tint: string; border: string; label: string };

const ESTILO_POR_SEVERIDAD: Record<NivelSeveridad, EstiloTarjeta> = {
  normal: {
    color: "var(--color-normal)",
    tint: "var(--tint-normal)",
    border: "var(--border-normal)",
    label: "ESTABLE",
  },
  precaucion: {
    color: "var(--color-precaucion)",
    tint: "var(--tint-precaucion)",
    border: "var(--border-precaucion)",
    label: "PRECAUCIÓN",
  },
  critica: {
    color: "var(--color-critica)",
    tint: "var(--tint-critica)",
    border: "var(--border-critica)",
    label: "CRÍTICO",
  },
};

// Un paciente dado de alta no está bajo monitoreo. Mostrar su última
// severidad_actual (que puede haber quedado en "normal" desde antes del
// alta) daría a entender que ese dato sigue siendo relevante hoy. Por
// eso el alta PISA la severidad con un estilo neutro propio, sin
// importar qué valor haya quedado guardado en el digital twin.
const ESTILO_DADO_DE_ALTA: EstiloTarjeta = {
  color: "var(--color-alta)",
  tint: "var(--tint-alta)",
  border: "var(--border-alta)",
  label: "DADO DE ALTA",
};

function PatientCard({ paciente }: PatientCardProps) {
  const estaDadoDeAlta = paciente.estado === "dado_de_alta";

  const estilo = estaDadoDeAlta
    ? ESTILO_DADO_DE_ALTA
    : ESTILO_POR_SEVERIDAD[paciente.digital_twin.severidad_actual];

  // El parpadeo crítico tampoco aplica si el paciente ya no está
  // internado, aunque su severidad guardada fuera "critica".
  const esCritica = !estaDadoDeAlta && paciente.digital_twin.severidad_actual === "critica";

  return (
    <Link
      to={`/pacientes/${paciente.id}`}
      style={{
        position: "relative",
        display: "block",
        textDecoration: "none",
        color: "inherit",
        padding: "17px 17px 17px 20px",
        borderRadius: "14px",
        background: "linear-gradient(165deg, var(--bg-panel), var(--bg-panel-alt))",
        border: `1px solid ${estilo.border}`,
        boxShadow: `0 0 0 1px rgba(0,0,0,.4), 0 0 22px ${estilo.tint}`,
        opacity: estaDadoDeAlta ? 0.55 : 1, // atenuada: comunica "inactivo" de un vistazo
      }}
    >
      <span
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: "3px",
          borderRadius: "14px 0 0 14px",
          background: estilo.color,
          boxShadow: `0 0 10px ${estilo.color}`,
          animation: esCritica ? "critblink 1.1s ease-in-out infinite" : undefined,
        }}
      />

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
        <strong style={{ fontSize: "15px", color: "var(--text-h)" }}>
          {paciente.nombre} {paciente.apellido}
        </strong>
        <span
          style={{
            padding: "4px 9px",
            borderRadius: "6px",
            fontFamily: "var(--mono)",
            fontSize: "9.5px",
            letterSpacing: ".14em",
            fontWeight: 600,
            color: estilo.color,
            background: estilo.tint,
            border: `1px solid ${estilo.border}`,
            whiteSpace: "nowrap",
          }}
        >
          {estilo.label}
        </span>
      </div>

      <p style={{ margin: "8px 0 0", fontSize: "13px", color: "var(--text-muted)", fontFamily: "var(--mono)" }}>
        {estaDadoDeAlta
          ? "Sin asignación activa"
          : `Sala ${paciente.sala ?? "s/asignar"} · Cama ${paciente.cama ?? "-"}`}
      </p>
    </Link>
  );
}

export default PatientCard;
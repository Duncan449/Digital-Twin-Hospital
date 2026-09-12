import { Link } from "react-router-dom";
import type { Alerta, TipoSignoVital } from "../types/clinico";
import type { Paciente } from "../types/pacientes";

interface AlertasActivasProps {
  alertas: Alerta[];
  pacientes: Paciente[];
  tiposSignosVitales: TipoSignoVital[];
}

// Traducción rápida de nombre técnico a nombre legible, para mostrar en la UI.
function nombreLegible(nombreTecnico: string): string {
  const texto = nombreTecnico.replace(/_/g, " ");
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

function AlertasActivas({ alertas, pacientes, tiposSignosVitales }: AlertasActivasProps) {
  if (alertas.length === 0) return null;

  return (
    <div
      style={{
        padding: "13px 16px",
        marginBottom: "20px",
        borderRadius: "12px",
        background: "linear-gradient(90deg, rgba(239,68,68,.18), rgba(239,68,68,.04))",
        border: "1px solid var(--border-critica)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <span
          style={{
            width: "9px",
            height: "9px",
            borderRadius: "50%",
            background: "var(--color-critica)",
            boxShadow: "0 0 10px var(--color-critica)",
            animation: "critblink 1.1s ease-in-out infinite",
            flex: "none",
          }}
        />
        <strong style={{ color: "var(--text-h)", fontSize: "14px" }}>
          {alertas.length} alerta{alertas.length > 1 ? "s" : ""} activa
          {alertas.length > 1 ? "s" : ""}
        </strong>
      </div>

      <ul style={{ margin: "10px 0 0", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "6px" }}>
        {alertas.map((alerta) => {
          const paciente = pacientes.find((p) => p.id === alerta.paciente_id);
          const tipoSigno = tiposSignosVitales.find(
            (t) => t.id === alerta.tipo_signo_id,
          );
          return (
            <li key={alerta.id}>
              <Link
                to={`/pacientes/${alerta.paciente_id}`}
                style={{ color: "var(--text)", fontSize: "13px" }}
              >
                <span
                  style={{ color: "var(--color-critica)", fontWeight: 600 }}
                >
                  {paciente
                    ? `${paciente.nombre} ${paciente.apellido}`
                    : "Paciente"}
                </span>
                {" — "}
                {alerta.severidad}
                {tipoSigno && ` — ${nombreLegible(tipoSigno.nombre)}`}
                {" ("}
                {alerta.valor_detectado ?? "?"}
                {tipoSigno && ` ${tipoSigno.unidad}`}
                {")"}
                {alerta.workflow_id_temporal === null && (
                  <span
                    style={{
                      marginLeft: "6px",
                      fontFamily: "var(--mono)",
                      fontSize: "10.5px",
                      color: "var(--text-muted)",
                    }}
                  >
                    ⚠ sin workflow
                  </span>
                )}
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default AlertasActivas;
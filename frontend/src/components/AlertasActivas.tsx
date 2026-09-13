import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Alerta } from "../types/clinico";
import type { Paciente } from "../types/pacientes";

interface AlertasActivasProps {
  alertas: Alerta[];
  pacientes: Paciente[];
}

const SEGUNDOS_PARA_ESCALAR = 45;

function AlertasActivas({ alertas, pacientes }: AlertasActivasProps) {
  const [ahora, setAhora] = useState(() => Date.now());
  useEffect(() => {
    const intervalo = setInterval(() => setAhora(Date.now()), 5000);
    return () => clearInterval(intervalo);
  }, []);

  if (alertas.length === 0) return null;

  return (
    <div
      style={{
        padding: "13px 16px",
        marginBottom: "20px",
        borderRadius: "12px",
        background:
          "linear-gradient(90deg, rgba(239,68,68,.18), rgba(239,68,68,.04))",
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

      <ul
        style={{
          margin: "10px 0 0",
          padding: 0,
          listStyle: "none",
          display: "flex",
          flexDirection: "column",
          gap: "6px",
        }}
      >
        {alertas.map((alerta) => {
          const paciente = pacientes.find((p) => p.id === alerta.paciente_id);
          const segundosSinAtender =
            (ahora - new Date(alerta.creada_en).getTime()) / 1000;
          const estaEscalada = segundosSinAtender >= SEGUNDOS_PARA_ESCALAR;

          return (
            <li
              key={alerta.id}
              style={{
                borderRadius: "8px",
                padding: estaEscalada ? "5px 8px" : "0",
                background: estaEscalada
                  ? "var(--tint-escalada)"
                  : "transparent",
                border: estaEscalada
                  ? "1px solid var(--border-escalada)"
                  : "1px solid transparent",
              }}
            >
              <Link
                to={`/pacientes/${alerta.paciente_id}`}
                style={{
                  color: "var(--text)",
                  fontSize: "13px",
                  display: "flex",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "6px",
                }}
              >
                {estaEscalada && (
                  <span
                    style={{
                      fontFamily: "var(--mono)",
                      fontSize: "9px",
                      fontWeight: 700,
                      letterSpacing: ".08em",
                      color: "var(--color-escalada)",
                      background: "var(--tint-escalada)",
                      border: "1px solid var(--border-escalada)",
                      borderRadius: "4px",
                      padding: "2px 6px",
                      animation: "critblink 1.4s ease-in-out infinite",
                      flex: "none",
                    }}
                  >
                    SIN ATENDER
                  </span>
                )}
                <span
                  style={{ color: "var(--color-critica)", fontWeight: 600 }}
                >
                  {paciente
                    ? `${paciente.nombre} ${paciente.apellido}`
                    : "Paciente"}
                </span>
                {" — "}
                {alerta.severidad} ({alerta.valor_detectado ?? "?"})
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default AlertasActivas;

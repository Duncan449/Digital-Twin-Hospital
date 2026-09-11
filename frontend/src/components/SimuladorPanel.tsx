import { useEffect, useState } from "react";
import { apiFetch } from "../services/apiFetch";
import { COLOR_SEVERIDAD } from "../constants/severidad";
import type { Paciente } from "../types/pacientes";
import type { TipoSignoVital } from "../types/clinico";

// Panel global del simulador: vive en Layout, por eso aparece tanto en
// el Dashboard como en el Digital Twin de cualquier paciente. A
// diferencia del resto de la app (que todavía está en Fase 3, con
// datos mock), ESTE componente pega directo contra el backend real --
// no tendría sentido "simular" el deterioro de un paciente que no
// existe en la base. Por eso usa apiFetch acá mismo en vez de un hook
// con mock, y por eso mismo puede mostrar datos que no coinciden
// exactamente con el Dashboard hasta que la Fase 4 lo alcance.
//
// Estilo tomado del mockup de referencia del proyecto (panel lateral
// oscuro, lista de objetivos con punto de color, botones de acción
// grandes). A propósito NO copiamos el pie de "ws://.../latencia" del
// mockup: eso implicaría una conexión WebSocket en vivo que recién
// llega en la Fase 5.

type EstadoBoton = "idle" | "cargando" | "hecho" | "error";

// Ancho del panel, en un solo lugar: Layout.tsx lo importa para saber
// cuánto tiene que "empujar" el contenido cuando el panel está abierto,
// así nunca puede desincronizarse del ancho real del <aside>.
export const ANCHO_PANEL_SIMULADOR = 340;

// El backend guarda "nombre" en snake_case (frecuencia_cardiaca, etc.)
// -- correcto para el catálogo, pero no para mostrárselo a un humano.
// Este mapa traduce cada nombre real a una etiqueta legible + un color
// propio, para que los 6 botones se distingan entre sí de un vistazo
// en vez de ser 6 bloques rojos iguales. Paleta y estilo (borde/fondo
// en rgba con la misma opacidad que el color) tomados del mockup de
// referencia del proyecto.
interface EstiloSigno {
  etiqueta: string;
  color: string;
  borde: string;
  tinte: string;
}

const ESTILO_SIGNO: Record<string, EstiloSigno> = {
  frecuencia_cardiaca: {
    etiqueta: "Frecuencia cardíaca",
    color: "#FCA5A5",
    borde: "rgba(239,68,68,.5)",
    tinte: "rgba(239,68,68,.12)",
  },
  frecuencia_respiratoria: {
    etiqueta: "Frecuencia respiratoria",
    color: "#FCA5A5",
    borde: "rgba(239,68,68,.5)",
    tinte: "rgba(239,68,68,.12)",
  },
  temperatura_corporal: {
    etiqueta: "Temperatura corporal",
    color: "#FCA5A5",
    borde: "rgba(239,68,68,.5)",
    tinte: "rgba(239,68,68,.12)",
  },
  saturacion_oxigeno: {
    etiqueta: "Saturación de oxígeno",
    color: "#FCA5A5",
    borde: "rgba(239,68,68,.5)",
    tinte: "rgba(239,68,68,.12)",
  },
  presion_sistolica: {
    etiqueta: "Presión sistólica",
    color: "#FCA5A5",
    borde: "rgba(239,68,68,.5)",
    tinte: "rgba(239,68,68,.12)",
  },
  presion_diastolica: {
    etiqueta: "Presión diastólica",
    color: "#FCA5A5",
    borde: "rgba(239,68,68,.5)",
    tinte: "rgba(239,68,68,.12)",
  },
};

// Fallback defensivo: si el catálogo suma un tipo nuevo que todavía no
// está mapeado arriba, no rompe -- muestra el nombre crudo con un
// estilo neutro en vez de un botón sin texto o que tira error.
const ESTILO_SIGNO_DEFAULT: EstiloSigno = {
  etiqueta: "",
  color: "var(--text-h)",
  borde: "var(--border)",
  tinte: "transparent",
};

// Un ícono de línea distinto por tipo, en el mismo estilo (SVG,
// stroke, sin relleno) que usa el mockup de referencia para sus
// botones de acción -- así también se distinguen visualmente, no solo
// por color.
function IconoSigno({ nombre, color }: { nombre: string; color: string }) {
  const props = {
    width: 15,
    height: 15,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: color,
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  switch (nombre) {
    case "frecuencia_cardiaca":
      return (
        <svg {...props}>
          <path d="M3 12h4l2-7 4 14 2-7h6" />
        </svg>
      );
    case "frecuencia_respiratoria":
      return (
        <svg {...props}>
          <path d="M3 9c2 0 2 3 4 3s2-3 4-3 2 3 4 3 2-3 4-3 2 3 4 3" />
        </svg>
      );
    case "temperatura_corporal":
      return (
        <svg {...props}>
          <path d="M12 14.5V5a2 2 0 1 0-4 0v9.5a4 4 0 1 0 4 0Z" />
        </svg>
      );
    case "saturacion_oxigeno":
      return (
        <svg {...props}>
          <path d="M12 3s6 6.4 6 10.4A6 6 0 0 1 6 13.4C6 9.4 12 3 12 3Z" />
        </svg>
      );
    case "presion_sistolica":
      return (
        <svg {...props}>
          <path d="M12 19V5M6 11l6-6 6 6" />
        </svg>
      );
    case "presion_diastolica":
      return (
        <svg {...props}>
          <path d="M12 5v14M6 13l6 6 6-6" />
        </svg>
      );
    default:
      return (
        <svg {...props}>
          <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z" />
        </svg>
      );
  }
}

interface SimuladorPanelProps {
  abierto: boolean;
  alAbrir: () => void;
  alCerrar: () => void;
}

function SimuladorPanel({ abierto, alAbrir, alCerrar }: SimuladorPanelProps) {
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [cargandoPacientes, setCargandoPacientes] = useState(true);

  const [tipos, setTipos] = useState<TipoSignoVital[]>([]);
  const [cargandoTipos, setCargandoTipos] = useState(true);

  const [pacienteSeleccionadoId, setPacienteSeleccionadoId] = useState<
    string | null
  >(null);

  // Un estado de botón por tipo_signo_id, para dar feedback puntual
  // sin bloquear el resto del panel mientras un solo click está en vuelo.
  const [estadoBotones, setEstadoBotones] = useState<
    Record<string, EstadoBoton>
  >({});
  const [estadoEstabilizar, setEstadoEstabilizar] =
    useState<EstadoBoton>("idle");

  useEffect(() => {
    apiFetch("/pacientes")
      .then((res) => res.json())
      .then((json: Paciente[]) => setPacientes(json))
      .catch(() => setPacientes([]))
      .finally(() => setCargandoPacientes(false));

    apiFetch("/tipos-signos-vitales")
      .then((res) => res.json())
      .then((json: TipoSignoVital[]) => setTipos(json))
      .catch(() => setTipos([]))
      .finally(() => setCargandoTipos(false));
  }, []);

  function marcarBoton(clave: string, estado: EstadoBoton) {
    setEstadoBotones((previo) => ({ ...previo, [clave]: estado }));
    if (estado === "hecho" || estado === "error") {
      setTimeout(() => {
        setEstadoBotones((previo) => ({ ...previo, [clave]: "idle" }));
      }, 1500);
    }
  }

  async function dispararDeterioro(tipoSignoId: string) {
    if (!pacienteSeleccionadoId) return;
    marcarBoton(tipoSignoId, "cargando");
    try {
      const res = await apiFetch(
        `/pacientes/${pacienteSeleccionadoId}/signos-vitales/${tipoSignoId}/deteriorar`,
        { method: "POST" },
      );
      marcarBoton(tipoSignoId, res.ok ? "hecho" : "error");
    } catch {
      marcarBoton(tipoSignoId, "error");
    }
  }

  async function estabilizarTodos() {
    setEstadoEstabilizar("cargando");
    try {
      const res = await apiFetch("/alertas/estabilizar-todos", {
        method: "POST",
      });
      setEstadoEstabilizar(res.ok ? "hecho" : "error");
    } catch {
      setEstadoEstabilizar("error");
    }
    setTimeout(() => setEstadoEstabilizar("idle"), 2000);
  }

  const etiquetaBoton: Record<EstadoBoton, string> = {
    idle: "",
    cargando: "…",
    hecho: "✓",
    error: "✕",
  };

  return (
    <>
      {!abierto && (
        <button
          onClick={alAbrir}
          style={{
            position: "fixed",
            top: "50%",
            right: 0,
            transform: "translateY(-50%)",
            zIndex: 30,
            writingMode: "vertical-rl",
            padding: "14px 6px",
            borderRadius: "8px 0 0 8px",
            border: "1px solid var(--border)",
            borderRight: "none",
            background: "var(--bg-panel-alt)",
            color: "var(--text-h)",
            fontFamily: "var(--mono)",
            fontSize: 11,
            letterSpacing: ".1em",
            cursor: "pointer",
          }}
        >
          SIMULADOR
        </button>
      )}

      <aside
        style={{
          position: "fixed",
          top: 0,
          right: abierto ? 0 : -ANCHO_PANEL_SIMULADOR,
          width: ANCHO_PANEL_SIMULADOR,
          height: "100vh",
          overflowY: "auto",
          background: "linear-gradient(180deg, #0D1729, #080F1C)",
          borderLeft: "1px solid var(--border)",
          padding: "18px 16px 28px",
          zIndex: 25,
          transition: "right 0.2s ease",
        }}
      >
        {/* Header: icono + título + tag DEMO + cerrar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginBottom: 4,
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path
              d="M3 12h4l2-7 4 14 2-7h6"
              stroke="var(--accent)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <div style={{ fontSize: 15, fontWeight: 700, flex: 1 }}>
            Simulador
          </div>
          <span
            style={{
              fontFamily: "var(--mono)",
              fontSize: 9.5,
              letterSpacing: ".08em",
              color: "var(--text-muted)",
              border: "1px solid var(--border)",
              borderRadius: 5,
              padding: "2px 6px",
            }}
          >
            DEMO
          </span>
          <button
            onClick={alCerrar}
            aria-label="Cerrar panel del simulador"
            style={{
              border: "1px solid var(--border)",
              background: "transparent",
              color: "var(--text-muted)",
              borderRadius: 6,
              width: 24,
              height: 24,
              cursor: "pointer",
              fontSize: 13,
              lineHeight: 1,
              flexShrink: 0,
            }}
          >
            ×
          </button>
        </div>

        {/* Acción global */}
        <button
          onClick={estabilizarTodos}
          disabled={estadoEstabilizar === "cargando"}
          style={{
            width: "100%",
            padding: "11px 12px",
            borderRadius: 9,
            border: "1px solid var(--border-normal)",
            background: "var(--tint-normal)",
            color: "var(--color-normal)",
            fontSize: 12.5,
            fontWeight: 700,
            cursor: "pointer",
            marginBottom: 20,
            marginTop: 20,
          }}
        >
          Estabilizar todos los pacientes {etiquetaBoton[estadoEstabilizar]}
        </button>

        {/* Lista de pacientes, con punto de color = severidad real */}
        <div
          style={{
            fontFamily: "var(--mono)",
            fontSize: 10,
            color: "var(--text-muted)",
            letterSpacing: ".1em",
            marginBottom: 8,
          }}
        >
          PACIENTE OBJETIVO
        </div>

        {cargandoPacientes ? (
          <p style={{ fontSize: 12.5 }}>Cargando...</p>
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 4,
              marginBottom: 20,
            }}
          >
            {pacientes.map((p) => (
              <button
                key={p.id}
                onClick={() => setPacienteSeleccionadoId(p.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 9,
                  textAlign: "left",
                  padding: "9px 10px",
                  borderRadius: 7,
                  border:
                    pacienteSeleccionadoId === p.id
                      ? "1px solid rgba(225, 232, 235, 0.5)"
                      : "1px solid var(--border)",
                  background:
                    pacienteSeleccionadoId === p.id
                      ? "rgba(225, 232, 235,.08)"
                      : "transparent",
                  color: "var(--text-h)",
                  fontSize: 12.5,
                  cursor: "pointer",
                }}
              >
                <span
                  style={{
                    width: 7,
                    height: 7,
                    borderRadius: "50%",
                    background:
                      COLOR_SEVERIDAD[p.digital_twin.severidad_actual],
                    flexShrink: 0,
                  }}
                />
                {p.nombre} {p.apellido}
              </button>
            ))}
            {pacientes.length === 0 && (
              <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                No hay pacientes internados.
              </p>
            )}
          </div>
        )}

        {/* Botones de deterioro, uno por tipo de signo del catálogo real */}
        <div
          style={{
            fontFamily: "var(--mono)",
            fontSize: 10,
            color: "var(--text-muted)",
            letterSpacing: ".1em",
            marginBottom: 8,
          }}
        >
          DETERIORAR SIGNO VITAL
        </div>

        {!pacienteSeleccionadoId ? (
          <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Elegí un paciente de la lista.
          </p>
        ) : cargandoTipos ? (
          <p style={{ fontSize: 12.5 }}>Cargando...</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {tipos.map((tipo) => {
              const estilo = ESTILO_SIGNO[tipo.nombre] ?? {
                ...ESTILO_SIGNO_DEFAULT,
                etiqueta: tipo.nombre,
              };
              return (
                <button
                  key={tipo.id}
                  onClick={() => dispararDeterioro(tipo.id)}
                  disabled={estadoBotones[tipo.id] === "cargando"}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 10,
                    padding: "10px 12px",
                    borderRadius: 9,
                    border: `1px solid ${estilo.borde}`,
                    background: estilo.tinte,
                    color: estilo.color,
                    fontSize: 12.5,
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  <span
                    style={{ display: "flex", alignItems: "center", gap: 9 }}
                  >
                    <IconoSigno nombre={tipo.nombre} color={estilo.color} />
                    {estilo.etiqueta}
                  </span>
                  <span>{etiquetaBoton[estadoBotones[tipo.id] ?? "idle"]}</span>
                </button>
              );
            })}
          </div>
        )}
      </aside>
    </>
  );
}

export default SimuladorPanel;

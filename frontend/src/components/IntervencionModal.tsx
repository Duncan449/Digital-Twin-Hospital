import { useState } from "react";
import { useIntervenciones } from "../hooks/useIntervenciones";
import type { IntervencionRespuesta } from "../types/intervencion";
import type { Alerta } from "../types/clinico";
import type { Paciente } from "../types/pacientes";

interface IntervencionModalProps {
  abierto: boolean;
  alerta: Alerta;
  paciente: Paciente;
  onCerrar: () => void;
  onExito: (resultado: IntervencionRespuesta) => void;
}

function IntervencionModal({
  abierto,
  alerta,
  paciente,
  onCerrar,
  onExito,
}: IntervencionModalProps) {
  const [accion, setAccion] = useState("");
  const [observaciones, setObservaciones] = useState("");
  const { enviarIntervencion, enviando, error } = useIntervenciones();

  if (!abierto) return null;

  const horaAlerta = new Date(alerta.creada_en).toLocaleTimeString("es-AR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const cama = paciente.cama ?? "SIN CAMA";

  async function manejarSubmit() {
    const resultado = await enviarIntervencion(alerta.id, {
      accion,
      observaciones: observaciones.trim() || null,
    });
    if (resultado) {
      setAccion("");
      setObservaciones("");
      onExito(resultado);
    }
  }

  return (
    <div
      onClick={onCerrar}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(3, 6, 12, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 420,
          maxWidth: "90vw",
          background: "var(--bg-panel)",
          border: "1px solid var(--border-critica)",
          borderRadius: 14,
          boxShadow: "0 0 40px rgba(239, 68, 68, 0.15)",
          padding: 22,
          fontFamily: "var(--sans)",
          color: "var(--text-h)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: 18,
          }}
        >
          <div>
            <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>
              Intervención médica
            </h2>
            <p
              style={{
                margin: "4px 0 0",
                fontFamily: "var(--mono)",
                fontSize: 11.5,
                color: "var(--color-critica)",
                letterSpacing: "0.03em",
              }}
            >
              {paciente.nombre} {paciente.apellido} · CAMA {cama} · {horaAlerta}
            </p>
          </div>
          <button
            onClick={onCerrar}
            aria-label="Cerrar"
            style={{
              background: "transparent",
              border: "1px solid var(--border)",
              borderRadius: 6,
              color: "var(--text-h)",
              width: 28,
              height: 28,
              cursor: "pointer",
            }}
          >
            ✕
          </button>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label
            htmlFor="accion"
            style={{
              display: "block",
              fontFamily: "var(--mono)",
              fontSize: 10.5,
              letterSpacing: "0.08em",
              color: "var(--text-muted)",
              marginBottom: 6,
              textTransform: "uppercase",
            }}
          >
            Acción tomada
          </label>
          <input
            id="accion"
            type="text"
            placeholder="Ej. Oxigenoterapia + bolo de adenosina"
            value={accion}
            onChange={(e) => setAccion(e.target.value)}
            style={{
              width: "100%",
              background: "var(--bg-panel-alt)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 8,
              padding: "10px 12px",
              color: "var(--text-h)",
              fontFamily: "var(--sans)",
              fontSize: 14,
              boxSizing: "border-box",
            }}
          />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label
            htmlFor="observaciones"
            style={{
              display: "block",
              fontFamily: "var(--mono)",
              fontSize: 10.5,
              letterSpacing: "0.08em",
              color: "var(--text-muted)",
              marginBottom: 6,
              textTransform: "uppercase",
            }}
          >
            Observaciones
          </label>
          <textarea
            id="observaciones"
            placeholder="Respuesta del paciente, constantes tras la maniobra..."
            value={observaciones}
            onChange={(e) => setObservaciones(e.target.value)}
            rows={4}
            style={{
              width: "100%",
              background: "var(--bg-panel-alt)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 8,
              padding: "10px 12px",
              color: "var(--text-h)",
              fontFamily: "var(--sans)",
              fontSize: 14,
              resize: "none",
              boxSizing: "border-box",
            }}
          />
        </div>

        {error && (
          <p
            style={{
              color: "var(--color-critica)",
              fontSize: 12.5,
              margin: "-8px 0 12px",
            }}
          >
            {error}
          </p>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
          <button
            onClick={onCerrar}
            disabled={enviando}
            style={{
              padding: "10px 18px",
              borderRadius: 8,
              fontFamily: "var(--sans)",
              fontWeight: 600,
              fontSize: 13.5,
              cursor: enviando ? "not-allowed" : "pointer",
              opacity: enviando ? 0.5 : 1,
              background: "transparent",
              border: "1px solid var(--border)",
              color: "var(--text-h)",
            }}
          >
            Cancelar
          </button>
          <button
            onClick={manejarSubmit}
            disabled={enviando || !accion.trim()}
            style={{
              padding: "10px 18px",
              borderRadius: 8,
              fontFamily: "var(--sans)",
              fontWeight: 600,
              fontSize: 13.5,
              cursor: enviando || !accion.trim() ? "not-allowed" : "pointer",
              opacity: enviando || !accion.trim() ? 0.5 : 1,
              background: "var(--color-normal)",
              border: "1px solid var(--color-normal)",
              color: "#06120C",
            }}
          >
            {enviando ? "Enviando..." : "Aceptar"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default IntervencionModal;

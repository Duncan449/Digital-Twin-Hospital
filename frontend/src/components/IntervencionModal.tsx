import { useState } from "react";
import { useIntervenciones } from "../hooks/useIntervenciones";
import type { Alerta } from "../types/clinico";
import type { Paciente } from "../types/pacientes";

interface IntervencionModalProps {
  abierto: boolean;
  alertas: Alerta[]; // TODAS las alertas activas del paciente, no una sola
  paciente: Paciente;
  onCerrar: () => void;
  // Se llama con los ids de alerta que SÍ se resolvieron, aunque no
  // hayan sido todas -- así el padre puede actualizar el estado
  // optimista de forma parcial si hubo fallos.
  onExito: (alertaIdsResueltos: string[]) => void;
}

function IntervencionModal({
  abierto,
  alertas,
  paciente,
  onCerrar,
  onExito,
}: IntervencionModalProps) {
  const [accion, setAccion] = useState("");
  const [observaciones, setObservaciones] = useState("");
  const { enviarIntervencionATodas, enviando, error } = useIntervenciones();

  if (!abierto || alertas.length === 0) return null;

  const cama = paciente.cama ?? "SIN CAMA";
  const cantidad = alertas.length;
  const etiquetaCantidad =
    cantidad === 1 ? "1 alerta activa" : `${cantidad} alertas activas`;

  async function manejarSubmit() {
    const resultado = await enviarIntervencionATodas(
      alertas.map((a) => a.id),
      { accion, observaciones: observaciones.trim() || null },
    );

    if (resultado.exitosas.length > 0) {
      onExito(resultado.exitosas.map((r) => r.alerta_id));
    }
    // Solo cerramos y limpiamos el formulario si TODAS se resolvieron.
    // Si hubo fallos parciales, el modal queda abierto mostrando el
    // error (viene de useIntervenciones) para que el usuario reintente.
    if (resultado.fallidas.length === 0) {
      setAccion("");
      setObservaciones("");
      onCerrar();
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
              {paciente.nombre} {paciente.apellido} · CAMA {cama} ·{" "}
              {etiquetaCantidad}
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

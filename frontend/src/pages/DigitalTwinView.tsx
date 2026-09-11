import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { usePaciente } from "../hooks/usePaciente";
import { useSignosVitales } from "../hooks/useSignosVitales";
import { useTiposSignosVitales } from "../hooks/useTiposSignosVitales";
import { useEventos } from "../hooks/useEventos";
import { useAlertas } from "../hooks/useAlertas";
import SeveridadBadge from "../components/SeveridadBadge";
import VitalSignCard from "../components/VitalSignCard";
import VitalSignChart from "../components/VitalSignChart";
import EventoTimeline from "../components/EventoTimeline";
import IntervencionModal from "../components/IntervencionModal";
import { BORDE_SEVERIDAD, GLOW_SEVERIDAD } from "../constants/severidad";
import type { SignoVital } from "../types/clinico";
import type { IntervencionRespuesta } from "../types/intervencion";

const VENTANA_GRAFICO_MS = 2 * 60 * 60 * 1000; // gráfico de 24 horas

function filtrarVentanaGrafico(historial: SignoVital[]): SignoVital[] {
  const corte = Date.now() - VENTANA_GRAFICO_MS;
  return historial.filter((m) => new Date(m.medido_en).getTime() >= corte);
}

function DigitalTwinView() {
  const { id } = useParams<{ id: string }>();
  const pacienteId = id ?? "";

  const paciente = usePaciente(pacienteId);
  const signosVitales = useSignosVitales(pacienteId);
  const tiposSignosVitales = useTiposSignosVitales();
  const eventos = useEventos(pacienteId);
  const alertas = useAlertas();

  const [modalAbierto, setModalAbierto] = useState(false);
  // Optimista: hasta que la Fase 5 conecte el WS "alerta_resuelta", así
  // ocultamos el botón apenas se confirma la intervención sin esperar
  // a que el backend termine de resolver la alerta de forma asíncrona.
  const [alertasIntervenidas, setAlertasIntervenidas] = useState<Set<string>>(
    new Set(),
  );

  if (paciente.loading)
    return <p style={{ padding: 22 }}>Cargando paciente...</p>;
  if (paciente.error)
    return <p style={{ padding: 22 }}>Error: {paciente.error}</p>;
  if (!paciente.data) return null;

  const severidad = paciente.data.digital_twin.severidad_actual;

  const alertaActiva = alertas.data.find(
    (a) => a.paciente_id === pacienteId && !alertasIntervenidas.has(a.id),
  );

  function manejarExitoIntervencion(resultado: IntervencionRespuesta) {
    setAlertasIntervenidas((previas) => {
      const siguientes = new Set(previas);
      siguientes.add(resultado.alerta_id);
      return siguientes;
    });
    setModalAbierto(false);
  }

  // Agrupamos el historial plano por tipo_signo_id: sin esto no hay
  // forma de saber cuál es "la última FC" vs "la última saturación".
  //
  // El backend devuelve signosVitales.data en orden DESCENDENTE
  // (medido_en DESC -- la más reciente primero; ver
  // listar_signos_vitales_paciente en el backend). Pero tanto
  // VitalSignCard (que toma historial[length-1] como "la última
  // medición") como VitalSignChart (que espera orden ascendente para
  // dibujar la línea de tiempo de izquierda a derecha) asumen lo
  // contrario. Por eso ordenamos ASC acá, una sola vez, al armar el
  // Map -- así ningún componente hijo tiene que reordenar por su cuenta.
  const historialPorTipo = new Map<string, SignoVital[]>();
  for (const medicion of signosVitales.data) {
    const lista = historialPorTipo.get(medicion.tipo_signo_id) ?? [];
    lista.push(medicion);
    historialPorTipo.set(medicion.tipo_signo_id, lista);
  }
  for (const lista of historialPorTipo.values()) {
    lista.sort((a, b) => (a.medido_en < b.medido_en ? -1 : 1));
  }

  return (
    <div style={{ padding: "20px 22px 34px" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 14,
          flexWrap: "wrap",
          marginBottom: 20,
        }}
      >
        <Link
          to="/"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "9px 14px",
            borderRadius: 9,
            border: "1px solid #24344F",
            background: "#0E1728",
            color: "#A8BDD8",
            fontSize: 13,
            fontWeight: 600,
            textDecoration: "none",
          }}
        >
          ← Dashboard
        </Link>
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 12,
            flexWrap: "wrap",
          }}
        >
          <span style={{ fontSize: 24, fontWeight: 700 }}>
            {paciente.data.nombre} {paciente.data.apellido}
          </span>
          <span
            style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 11,
              color: "#5C7292",
              letterSpacing: "0.1em",
            }}
          >
            Sala {paciente.data.sala ?? "sin asignar"} · Cama{" "}
            {paciente.data.cama ?? "-"}
          </span>
        </div>
        <div
          style={{
            marginLeft: "auto",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          {alertaActiva && (
            <button
              onClick={() => setModalAbierto(true)}
              style={{
                padding: "9px 16px",
                borderRadius: 9,
                border: "1px solid var(--border-critica)",
                background: "var(--tint-critica)",
                color: "var(--color-critica)",
                fontSize: 13,
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Intervenir alerta activa
            </button>
          )}
          <SeveridadBadge severidad={severidad} />
        </div>
      </div>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 16,
          alignItems: "flex-start",
        }}
      >
        <div
          style={{
            flex: "3 1 460px",
            minWidth: 0,
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          {tiposSignosVitales.loading ? (
            <p>Cargando catálogo de signos vitales...</p>
          ) : (
            <>
              {/* Panel envolvente: mismo tratamiento que el mockup (borde +
                  glow según severidad), agrupa las tarjetas para que se
                  lean como "un solo bloque de telemetría", no sueltas. */}
              <div
                style={{
                  padding: 20,
                  borderRadius: 16,
                  background: "linear-gradient(160deg, #0D1729, #080F1C)",
                  border: `1px solid ${BORDE_SEVERIDAD[severidad]}`,
                  boxShadow: `0 0 34px ${GLOW_SEVERIDAD[severidad]}`,
                }}
              >
                <div
                  style={{
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontSize: 10.5,
                    letterSpacing: "0.18em",
                    color: "#5C7292",
                    marginBottom: 16,
                  }}
                >
                  GEMELO DIGITAL · SIGNOS VITALES
                </div>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                    gap: 14,
                  }}
                >
                  {tiposSignosVitales.data.map((tipo) => {
                    const historial = historialPorTipo.get(tipo.id) ?? [];
                    return (
                      <VitalSignCard
                        key={tipo.id}
                        tipo={tipo}
                        ultimaMedicion={historial[historial.length - 1]}
                      />
                    );
                  })}
                </div>
              </div>

              {tiposSignosVitales.data.map((tipo) => {
                const historialCompleto = historialPorTipo.get(tipo.id) ?? [];
                const historial = filtrarVentanaGrafico(historialCompleto);
                if (historial.length === 0) return null;
                return (
                  <VitalSignChart
                    key={tipo.id}
                    tipo={tipo}
                    historial={historial}
                  />
                );
              })}
            </>
          )}
        </div>

        <div
          style={{
            flex: "1 1 300px",
            minWidth: 0,
            padding: 18,
            borderRadius: 16,
            background: "#0B1423",
            border: "1px solid #1A2740",
            maxHeight: 760,
            overflowY: "auto",
          }}
        >
          <div style={{ fontSize: 15.5, fontWeight: 700 }}>
            Historial de eventos
          </div>
          <div
            style={{
              fontFamily: "'IBM Plex Mono', monospace",
              fontSize: 10,
              letterSpacing: "0.14em",
              color: "#5C7292",
              margin: "3px 0 15px",
            }}
          >
            REGISTRO CRONOLÓGICO
          </div>
          {eventos.loading ? (
            <p>Cargando eventos...</p>
          ) : (
            <EventoTimeline eventos={eventos.data} />
          )}
        </div>
      </div>

      {alertaActiva && (
        <IntervencionModal
          abierto={modalAbierto}
          alerta={alertaActiva}
          paciente={paciente.data}
          onCerrar={() => setModalAbierto(false)}
          onExito={manejarExitoIntervencion}
        />
      )}
    </div>
  );
}

export default DigitalTwinView;

// frontend/src/components/EventoTimeline.tsx
import type { Evento } from "../types/clinico";
import { COLOR_SEVERIDAD } from "../constants/severidad";

interface EventoTimelineProps {
  eventos: Evento[]; // ya ordenados, más reciente primero
}

const formateaHora = (iso: string) =>
  new Date(iso).toLocaleTimeString("es-AR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

const ETIQUETA_TIPO: Record<Evento["tipo"], string> = {
  registro_signo: "TELEMETRÍA",
  alerta_generada: "ALERTA",
  alerta_actualizada: "ALERTA",
  intervencion_registrada: "INTERVENCIÓN",
  paciente_creado: "SISTEMA",
  paciente_actualizado: "SISTEMA",
};

function EventoTimeline({ eventos }: EventoTimelineProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {eventos.map((evento, indice) => (
        <div
          key={evento.id}
          style={{ display: "grid", gridTemplateColumns: "20px 1fr", gap: 12 }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              paddingTop: 5,
            }}
          >
            <span
              style={{
                width: 9,
                height: 9,
                borderRadius: "50%",
                background: COLOR_SEVERIDAD[evento.severidad],
                boxShadow: `0 0 10px ${COLOR_SEVERIDAD[evento.severidad]}`,
                flex: "none",
              }}
            />
            {indice < eventos.length - 1 && (
              <span
                style={{
                  flex: "1 1 auto",
                  width: 1,
                  background: "#1B2942",
                  minHeight: 22,
                }}
              />
            )}
          </div>
          <div style={{ paddingBottom: 14 }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 9 }}>
              <span
                style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 11.5,
                  fontWeight: 600,
                  color: COLOR_SEVERIDAD[evento.severidad],
                }}
              >
                {formateaHora(evento.ocurrido_en)}
              </span>
              <span
                style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 9,
                  letterSpacing: "0.12em",
                  color: "#4A5F80",
                }}
              >
                {ETIQUETA_TIPO[evento.tipo]}
              </span>
            </div>
            <div
              style={{
                fontSize: 13.5,
                color: "#C6D5E8",
                marginTop: 3,
                lineHeight: 1.4,
              }}
            >
              {evento.descripcion}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default EventoTimeline;

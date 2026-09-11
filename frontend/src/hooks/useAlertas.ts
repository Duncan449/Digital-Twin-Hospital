import { useEffect, useState } from "react";
import type { Alerta } from "../types/clinico";
import { apiFetch } from "../services/apiFetch";
import { useEventosWebSocket } from "../context/EventosWebSocketContext";

interface UseAlertasResultado {
  data: Alerta[];
  loading: boolean;
  error: string | null;
}

const TIPOS_ALERTA = new Set([
  "alerta_generada",
  "alerta_actualizada",
  "alerta_resuelta",
]);

// El filtro por estado="activa" que antes vivía acá (sobre el mock)
// no vuelve: GET /alertas ya filtra por estado=activa del lado del
// backend por default.
export function useAlertas(): UseAlertasResultado {
  const [data, setData] = useState<Alerta[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { suscribir } = useEventosWebSocket();

  useEffect(() => {
    const controlador = new AbortController();

    async function cargarAlertas() {
      setLoading(true);
      setError(null);

      try {
        const respuesta = await apiFetch("/alertas", {
          signal: controlador.signal,
        });

        if (!respuesta.ok) {
          throw new Error(
            `El servidor respondió con estado ${respuesta.status}`,
          );
        }

        const json: Alerta[] = await respuesta.json();
        setData(json);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        setError("No se pudieron cargar las alertas.");
      } finally {
        setLoading(false);
      }
    }

    cargarAlertas();

    return () => controlador.abort();
  }, []);

  // Fase 5: en vez de re-pedir todo /alertas cada vez que algo cambia,
  // aplicamos el evento puntual sobre el array que ya tenemos en
  // memoria. Los 3 tipos que nos importan siempre traen "alerta_id"
  // adentro de data (ver signos_vitales_service.py / activities.py).
  useEffect(() => {
    return suscribir((evento) => {
      if (!TIPOS_ALERTA.has(evento.tipo)) return;

      const alertaId = evento.data.alerta_id as string | undefined;
      if (!alertaId) return;

      setData((previas) => {
        if (evento.tipo === "alerta_resuelta") {
          // GET /alertas por default solo trae estado=activa, así que
          // una alerta resuelta simplemente desaparece de esta lista.
          return previas.filter((a) => a.id !== alertaId);
        }

        const existente = previas.find((a) => a.id === alertaId);

        if (existente) {
          // alerta_actualizada sobre una que ya teníamos: pisamos solo
          // los campos que vienen en el evento.
          return previas.map((a) =>
            a.id === alertaId
              ? {
                  ...a,
                  severidad: evento.data.severidad as Alerta["severidad"],
                  valor_detectado:
                    (evento.data.valor_detectado as string) ?? null,
                  estado: evento.data.estado as Alerta["estado"],
                }
              : a,
          );
        }

        // alerta_generada (o una actualizada que llegó antes de que
        // terminara el fetch inicial): la agregamos como entrada nueva.
        // tipo_signo_id y workflow_id_temporal no viajan en este
        // evento -- quedan en null hasta el próximo fetch completo
        // (workflow_id_temporal, de hecho, todavía es null en el
        // backend en este preciso instante: recién se asigna después).
        const nueva: Alerta = {
          id: alertaId,
          paciente_id: evento.paciente_id,
          tipo_signo_id: null,
          severidad: evento.data.severidad as Alerta["severidad"],
          valor_detectado: (evento.data.valor_detectado as string) ?? null,
          estado: evento.data.estado as Alerta["estado"],
          workflow_id_temporal: null,
          creada_en: evento.timestamp,
          resuelta_en: null,
        };
        return [nueva, ...previas];
      });
    });
  }, [suscribir]);

  return { data, loading, error };
}

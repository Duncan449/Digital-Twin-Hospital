import { useCallback, useEffect, useRef, useState } from "react";
import type { Evento } from "../types/clinico";
import { apiFetch } from "../services/apiFetch";
import { useEventosWebSocket } from "../context/EventosWebSocketContext";

interface UseEventosResultado {
  data: Evento[];
  loading: boolean;
  error: string | null;
}

// Cuánto silencio esperamos antes de refetchear. En deteccion.py CADA 
// medición deja un Evento -- en una simulación de 60+ pasos eso son 60+ 
// eventos en pocos segundos. Sin este debounce, cada uno dispara un GET 
// completo del historial (que crece con cada evento), saturando al 
// navegador. Con el debounce, toda esa ráfaga colapsa en un solo refetch 
// cuando la ráfaga termina.
const DEMORA_DEBOUNCE_MS = 800;

export function useEventos(pacienteId: string): UseEventosResultado {
  const [data, setData] = useState<Evento[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { suscribir } = useEventosWebSocket();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cargarEventos = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);

      try {
        const respuesta = await apiFetch(`/pacientes/${pacienteId}/eventos`, {
          signal,
        });

        if (!respuesta.ok) {
          throw new Error(
            `El servidor respondió con estado ${respuesta.status}`,
          );
        }

        // El backend ya devuelve el historial "más reciente primero",
        // que es exactamente el orden que espera EventoTimeline.
        const json: Evento[] = await respuesta.json();
        setData(json);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        setError("No se pudo cargar el historial de eventos.");
      } finally {
        setLoading(false);
      }
    },
    [pacienteId],
  );

  useEffect(() => {
    const controlador = new AbortController();
    setData([]); // limpiamos el historial del paciente anterior al cambiar de id
    cargarEventos(controlador.signal);
    return () => controlador.abort();
  }, [cargarEventos]);

  // deteccion.py deja un Evento por CADA medición (no solo cuando hay
  // alerta), así que no reconstruimos el Evento a mano acá (no tenemos
  // ni su "id" real ni su "descripcion" en el payload del WS). En
  // cambio, acumulamos la señal de "algo cambió" y refetcheamos una
  // sola vez cuando la ráfaga de eventos se calma, en vez de una vez
  // por evento.
  useEffect(() => {
    return suscribir((evento) => {
      if (evento.paciente_id !== pacienteId) return;

      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        cargarEventos();
      }, DEMORA_DEBOUNCE_MS);
    });
  }, [suscribir, pacienteId, cargarEventos]);

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return { data, loading, error };
}
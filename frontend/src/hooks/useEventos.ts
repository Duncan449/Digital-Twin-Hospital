import { useEffect, useState } from "react";
import type { Evento } from "../types/clinico";
import { apiFetch } from "../services/apiFetch";

interface UseEventosResultado {
  data: Evento[];
  loading: boolean;
  error: string | null;
}

export function useEventos(pacienteId: string): UseEventosResultado {
  const [data, setData] = useState<Evento[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controlador = new AbortController();

    async function cargarEventos() {
      setLoading(true);
      setError(null);
      setData([]); // limpiamos el historial del paciente anterior al cambiar de id

      try {
        const respuesta = await apiFetch(`/pacientes/${pacienteId}/eventos`, {
          signal: controlador.signal,
        });

        if (!respuesta.ok) {
          throw new Error(
            `El servidor respondió con estado ${respuesta.status}`,
          );
        }

        // El backend ya devuelve el historial ordenado "más reciente
        // primero" (ORDER BY ocurrido_en DESC), que es exactamente el
        // orden que espera EventoTimeline -- a diferencia del historial
        // de signos vitales en DigitalTwinView, acá no hace falta
        // reordenar nada.
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
    }

    cargarEventos();

    return () => controlador.abort();
  }, [pacienteId]);

  return { data, loading, error };
}

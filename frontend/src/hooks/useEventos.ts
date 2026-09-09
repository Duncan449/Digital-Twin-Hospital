// frontend/src/hooks/useEventos.ts
import { useEffect, useState } from "react";
import type { Evento } from "../types/clinico";
import { eventosMock } from "../mocks/clinico";

interface UseEventosResultado {
  data: Evento[];
  loading: boolean;
  error: string | null;
}

const DELAY_SIMULADO_MS = 400;

export function useEventos(pacienteId: string): UseEventosResultado {
  const [data, setData] = useState<Evento[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setData([]);

    const temporizador = setTimeout(() => {
      // --- Hoy: mock. Mañana: ---
      // fetch(`http://localhost:8000/pacientes/${pacienteId}/eventos`)
      //   .then((res) => res.json())
      //   .then((json: Evento[]) => setData(json))
      //   .catch(() => setError("No se pudo cargar el historial de eventos."))
      //   .finally(() => setLoading(false));

      // El mock no viene pre-ordenado; el endpoint real sí devuelve
      // "más reciente primero" (ver listar_eventos_paciente), así que
      // ordenamos acá para que el mock se comporte igual.
      const historial = eventosMock
        .filter((e) => e.paciente_id === pacienteId)
        .slice()
        .sort((a, b) => (a.ocurrido_en < b.ocurrido_en ? 1 : -1));
      setData(historial);
      setLoading(false);
    }, DELAY_SIMULADO_MS);

    return () => clearTimeout(temporizador);
  }, [pacienteId]);

  return { data, loading, error };
}

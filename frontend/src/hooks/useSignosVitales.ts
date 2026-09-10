import { useEffect, useState } from "react";
import type { SignoVital } from "../types/clinico";
import { apiFetch } from "../services/apiFetch";

interface UseSignosVitalesResultado {
  data: SignoVital[];
  loading: boolean;
  error: string | null;
}

export function useSignosVitales(
  pacienteId: string,
): UseSignosVitalesResultado {
  const [data, setData] = useState<SignoVital[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controlador = new AbortController();

    async function cargarSignosVitales() {
      setLoading(true);
      setError(null);
      setData([]); // limpiamos el historial del paciente anterior al cambiar de id

      try {
        const respuesta = await apiFetch(
          `/pacientes/${pacienteId}/signos-vitales`,
          { signal: controlador.signal },
        );

        if (!respuesta.ok) {
          throw new Error(
            `El servidor respondió con estado ${respuesta.status}`,
          );
        }

        const json: SignoVital[] = await respuesta.json();
        setData(json);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        setError("No se pudo cargar el historial de signos vitales.");
      } finally {
        setLoading(false);
      }
    }

    cargarSignosVitales();

    return () => controlador.abort();
  }, [pacienteId]);

  return { data, loading, error };
}

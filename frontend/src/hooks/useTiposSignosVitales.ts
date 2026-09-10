import { useEffect, useState } from "react";
import type { TipoSignoVital } from "../types/clinico";
import { apiFetch } from "../services/apiFetch";

interface UseTiposSignosVitalesResultado {
  data: TipoSignoVital[];
  loading: boolean;
  error: string | null;
}

export function useTiposSignosVitales(): UseTiposSignosVitalesResultado {
  const [data, setData] = useState<TipoSignoVital[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controlador = new AbortController();

    async function cargarTipos() {
      setLoading(true);
      setError(null);

      try {
        const respuesta = await apiFetch("/tipos-signos-vitales", {
          signal: controlador.signal,
        });

        if (!respuesta.ok) {
          throw new Error(
            `El servidor respondió con estado ${respuesta.status}`,
          );
        }

        const json: TipoSignoVital[] = await respuesta.json();
        setData(json);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        setError("No se pudo cargar el catálogo de signos vitales.");
      } finally {
        setLoading(false);
      }
    }

    cargarTipos();

    return () => controlador.abort();
  }, []);

  return { data, loading, error };
}

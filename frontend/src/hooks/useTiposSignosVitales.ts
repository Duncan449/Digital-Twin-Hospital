// frontend/src/hooks/useTiposSignosVitales.ts
import { useEffect, useState } from "react";
import type { TipoSignoVital } from "../types/clinico";
import { tiposSignosVitalesMock } from "../mocks/clinico";

interface UseTiposSignosVitalesResultado {
  data: TipoSignoVital[];
  loading: boolean;
  error: string | null;
}

const DELAY_SIMULADO_MS = 400;

export function useTiposSignosVitales(): UseTiposSignosVitalesResultado {
  const [data, setData] = useState<TipoSignoVital[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const temporizador = setTimeout(() => {
      // --- Hoy: mock. Mañana: ---
      // fetch("http://localhost:8000/tipos-signos-vitales")
      //   .then((res) => res.json())
      //   .then((json: TipoSignoVital[]) => setData(json))
      //   .catch(() => setError("No se pudo cargar el catálogo de signos vitales."))
      //   .finally(() => setLoading(false));
      setData(tiposSignosVitalesMock);
      setLoading(false);
    }, DELAY_SIMULADO_MS);

    return () => clearTimeout(temporizador);
  }, []);

  return { data, loading, error };
}

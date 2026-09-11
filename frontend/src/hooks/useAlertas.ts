import { useEffect, useState } from "react";
import type { Alerta } from "../types/clinico";
import { apiFetch } from "../services/apiFetch";

interface UseAlertasResultado {
  data: Alerta[];
  loading: boolean;
  error: string | null;
}

// El filtro por estado="activa" que antes vivía acá (sobre el mock)
// desaparece: GET /alertas ya filtra por estado=activa del lado del
// backend por default (ver alertas_routes.py -- el query param
// "estado" tiene EstadoAlerta.activa como valor por defecto). Repetir
// el filtro acá sería lógica duplicada sin necesidad.
export function useAlertas(): UseAlertasResultado {
  const [data, setData] = useState<Alerta[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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

  return { data, loading, error };
}

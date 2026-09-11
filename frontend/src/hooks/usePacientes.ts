import { useEffect, useState } from "react";
import type { Paciente } from "../types/pacientes";
import { apiFetch } from "../services/apiFetch";

interface UsePacientesResultado {
  data: Paciente[];
  loading: boolean;
  error: string | null;
}

export function usePacientes(): UsePacientesResultado {
  const [data, setData] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controlador = new AbortController();

    async function cargarPacientes() {
      setLoading(true);
      setError(null);

      try {
        const respuesta = await apiFetch("/pacientes", {
          signal: controlador.signal,
        });

        if (!respuesta.ok) {
          throw new Error(
            `El servidor respondió con estado ${respuesta.status}`,
          );
        }

        const json: Paciente[] = await respuesta.json();
        setData(json);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        setError("No se pudieron cargar los pacientes.");
      } finally {
        setLoading(false);
      }
    }

    cargarPacientes();

    return () => controlador.abort();
  }, []);

  return { data, loading, error };
}

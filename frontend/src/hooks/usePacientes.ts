import { useCallback, useEffect, useState } from "react";
import type { Paciente } from "../types/pacientes";
import { apiFetch } from "../services/apiFetch";

interface UsePacientesResultado {
  data: Paciente[];
  loading: boolean;
  error: string | null;
  // Expuesto para que quien cree/edite/dé de alta a un paciente (en un
  // modal aparte, ver PacienteFormModal) pueda refrescar la lista sin
  // que este hook necesite saber nada de esas acciones.
  recargar: () => void;
}

export function usePacientes(): UsePacientesResultado {
  const [data, setData] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  // Cambiar este número es la señal para que el useEffect de abajo
  // vuelva a correr y pida los pacientes de nuevo.
  const [version, setVersion] = useState(0);

  const recargar = useCallback(() => {
    setVersion((v) => v + 1);
  }, []);

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
  }, [version]);

  return { data, loading, error, recargar };
}

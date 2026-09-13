import { useCallback, useEffect, useState } from "react";
import type { Paciente } from "../types/pacientes";
import { apiFetch } from "../services/apiFetch";

interface UsePacienteResultado {
  data: Paciente | null;
  loading: boolean;
  error: string | null;
  // Igual que en usePacientes: permite refrescar este paciente puntual
  // después de editarlo o darlo de alta desde PacienteFormModal.
  recargar: () => void;
}

export function usePaciente(pacienteId: string): UsePacienteResultado {
  const [data, setData] = useState<Paciente | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);

  const recargar = useCallback(() => {
    setVersion((v) => v + 1);
  }, []);

  useEffect(() => {
    const controlador = new AbortController();

    async function cargarPaciente() {
      setLoading(true);
      setError(null);
      setData(null); // limpiamos el paciente anterior al cambiar de id

      try {
        const respuesta = await apiFetch(`/pacientes/${pacienteId}`, {
          signal: controlador.signal,
        });

        // 404 es un caso esperado acá (id inválido o paciente borrado),
        // no un error de servidor -- lo distinguimos del resto de
        // estados no-ok para dar un mensaje más preciso.
        if (respuesta.status === 404) {
          setError(`No se encontró un paciente con id ${pacienteId}.`);
          return;
        }

        if (!respuesta.ok) {
          throw new Error(
            `El servidor respondió con estado ${respuesta.status}`,
          );
        }

        const json: Paciente = await respuesta.json();
        setData(json);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        setError("No se pudo cargar el paciente.");
      } finally {
        setLoading(false);
      }
    }

    cargarPaciente();

    return () => controlador.abort();
  }, [pacienteId, version]);

  return { data, loading, error, recargar };
}

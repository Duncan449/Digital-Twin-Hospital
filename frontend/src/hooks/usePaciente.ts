import { useEffect, useState } from "react";
import type { Paciente } from "../types/pacientes";
import { pacientesMock } from "../mocks/pacientes";

interface UsePacienteResultado {
  data: Paciente | null;
  loading: boolean;
  error: string | null;
}

const DELAY_SIMULADO_MS = 400;

// Trae un paciente puntual COMPLETO -- incluye su digital_twin anidado,
// porque así es como lo devuelve GET /pacientes/{id} en el backend real.
// Esto reemplaza al viejo useDigitalTwin: antes hacía falta un hook
// aparte para el twin porque no existía forma de pedirlo junto al
// paciente; ahora una sola llamada trae todo lo que necesita la
// pantalla del Digital Twin (nombre, sala, cama, y severidad_actual).
export function usePaciente(pacienteId: string): UsePacienteResultado {
  const [data, setData] = useState<Paciente | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setData(null); // limpiamos el paciente anterior al cambiar de id

    const temporizador = setTimeout(() => {
      // --- Hoy: mock. Mañana: ---
      // fetch(`http://localhost:8000/pacientes/${pacienteId}`)
      //   .then((res) => res.json())
      //   .then((json: Paciente) => setData(json))
      //   .catch(() => setError("No se pudo cargar el paciente."))
      //   .finally(() => setLoading(false));
      const paciente = pacientesMock.find((p) => p.id === pacienteId);

      if (paciente === undefined) {
        setError(`No se encontró un paciente con id ${pacienteId}.`);
      } else {
        setData(paciente);
      }
      setLoading(false);
    }, DELAY_SIMULADO_MS);

    return () => clearTimeout(temporizador);
  }, [pacienteId]);

  return { data, loading, error };
}

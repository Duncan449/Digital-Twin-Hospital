import { useEffect, useState } from "react";
import type { SignoVital } from "../types/clinico";
import { signosVitalesMock } from "../mocks/clinico";

interface UseSignosVitalesResultado {
  data: SignoVital[];
  loading: boolean;
  error: string | null;
}

const DELAY_SIMULADO_MS = 400;

// Igual que useDigitalTwin: recibe pacienteId como parámetro, porque el
// historial de mediciones es siempre "de un paciente puntual", nunca
// de todos a la vez (a diferencia de usePacientes, que sí trae la lista completa).
export function useSignosVitales(
  pacienteId: string,
): UseSignosVitalesResultado {
  const [data, setData] = useState<SignoVital[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setData([]); // limpiamos el historial del paciente anterior al cambiar de id

    const temporizador = setTimeout(() => {
      // --- Hoy: mock. Mañana: ---
      // fetch(`http://localhost:8000/pacientes/${pacienteId}/signos-vitales`)
      //   .then((res) => res.json())
      //   .then((json: SignoVital[]) => setData(json))
      //   .catch(() => setError("No se pudo cargar el historial de signos vitales."))
      //   .finally(() => setLoading(false));
      const historial = signosVitalesMock.filter(
        (s) => s.paciente_id === pacienteId,
      );
      setData(historial);
      setLoading(false);
    }, DELAY_SIMULADO_MS);

    return () => clearTimeout(temporizador);
  }, [pacienteId]);

  return { data, loading, error };
}

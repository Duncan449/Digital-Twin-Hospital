import { useEffect, useState } from "react";
import type { Paciente } from "../types/pacientes";
import { pacientesMock } from "../mocks/pacientes";

interface UsePacientesResultado {
  data: Paciente[];
  loading: boolean;
  error: string | null;
}

// Simula la latencia de una llamada real a la API. 400ms es suficiente
// para VER el estado "loading" en pantalla (si fuera instantáneo, no
// podrías comprobar que el spinner/mensaje de carga funciona).
const DELAY_SIMULADO_MS = 400;

export function usePacientes(): UsePacientesResultado {
  const [data, setData] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const temporizador = setTimeout(() => {
      // --- Hoy: mock. Mañana acá va el fetch real: ---
      // fetch("http://localhost:8000/pacientes")
      //   .then((res) => res.json())
      //   .then((json: Paciente[]) => setData(json))
      //   .catch(() => setError("No se pudieron cargar los pacientes."))
      //   .finally(() => setLoading(false));
      setData(pacientesMock);
      setLoading(false);
    }, DELAY_SIMULADO_MS);

    // Cleanup: si el componente se desmonta antes de que termine el
    // timeout (ej. el usuario navega rápido a otra pantalla), cancelamos
    // el temporizador para no llamar a setData sobre un componente que
    // ya no existe (React tira un warning en consola si no hacés esto).
    return () => clearTimeout(temporizador);
  }, []);

  return { data, loading, error };
}

import { useEffect, useState } from "react";
import type { Alerta } from "../types/clinico";
import { alertasMock } from "../mocks/clinico";

interface UseAlertasResultado {
  data: Alerta[];
  loading: boolean;
  error: string | null;
}

const DELAY_SIMULADO_MS = 400;

// Mismo patrón que usePacientes.ts. Filtramos por estado "activa" acá en
// el frontend porque el mock no discrimina, el backend real ya filtra 
// por estado=activa por default, así que este filtro
// desaparece solo cuando conectemos el fetch real en la Fase 4.
export function useAlertas(): UseAlertasResultado {
  const [data, setData] = useState<Alerta[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    const temporizador = setTimeout(() => {
      const activas = alertasMock.filter((a) => a.estado === "activa");
      setData(activas);
      setLoading(false);
    }, DELAY_SIMULADO_MS);

    return () => clearTimeout(temporizador);
  }, []);

  return { data, loading, error };
}
import { useEffect, useState } from "react";
import type { Paciente } from "../types/pacientes";
import { apiFetch } from "../services/apiFetch";
import { useEventosWebSocket } from "../context/EventosWebSocketContext";

interface UsePacientesResultado {
  data: Paciente[];
  loading: boolean;
  error: string | null;
}

// Eventos que traen un cambio real en digital_twin.severidad_actual:
// - alerta_generada/actualizada: cuando una medición dispara o
//   actualiza una alerta (deterioro).
// - medicion_registrada: se dispara en TODA medición, incluidas las
//   6 mediciones de la estabilización automática post-intervención
//   sin este evento, el punto se quedaba pegado en naranja/rojo porque 
//   durante la estabilización la alerta ya está resuelta y no hay ningún 
//  evento de tipo alerta.
const TIPOS_SEVERIDAD = new Set([
  "alerta_generada",
  "alerta_actualizada",
  "medicion_registrada",
]);

export function usePacientes(): UsePacientesResultado {
  const [data, setData] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { suscribir } = useEventosWebSocket();

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

  // Sin esto, digital_twin.severidad_actual queda con el valor
  // que tenía al montar el Dashboard -- por eso los KPIs (que leen
  // justo ese campo) no se movían aunque AlertasActivas sí reaccionaba.
  useEffect(() => {
    return suscribir((evento) => {
      if (!TIPOS_SEVERIDAD.has(evento.tipo)) return;

      const nuevaSeveridad = (evento.data.severidad ??
        evento.data.severidad_calculada) as
        | Paciente["digital_twin"]["severidad_actual"]
        | undefined;
      if (!nuevaSeveridad) return;

      setData((previos) =>
        previos.map((p) =>
          p.id === evento.paciente_id
            ? {
                ...p,
                digital_twin: {
                  ...p.digital_twin,
                  severidad_actual: nuevaSeveridad,
                },
              }
            : p,
        ),
      );
    });
  }, [suscribir]);

  return { data, loading, error };
}

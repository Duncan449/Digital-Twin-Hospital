import { useEffect, useState } from "react";
import type { Paciente } from "../types/pacientes";
import { apiFetch } from "../services/apiFetch";
import { useEventosWebSocket } from "../context/EventosWebSocketContext";

interface UsePacientesResultado {
  data: Paciente[];
  loading: boolean;
  error: string | null;
}

// Eventos que pueden significar un cambio en digital_twin.severidad_actual:
// - alerta_generada/actualizada: una medición dispara o actualiza una alerta.
// - medicion_registrada: se dispara en TODA medición, incluida la
//   estabilización post-intervención.
//
// A propósito NO tratamos de derivar la nueva severidad de ningún campo
// del evento (ej. "severidad_calculada"): ese campo es la severidad del
// SIGNO puntual que se acaba de medir, no la del paciente en su
// conjunto -- confundir esos dos valores fue justo el bug (una medición
// normal de un signo distinto pisaba el estado crítico de otro). El
// backend (deteccion.py) ya calcula correctamente severidad_actual como
// el máximo entre todas las alertas activas del paciente; acá solo le
// preguntamos ese resultado ya calculado, en vez de reinventarlo.
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

  useEffect(() => {
    return suscribir((evento) => {
      if (!TIPOS_SEVERIDAD.has(evento.tipo)) return;

      // Le preguntamos al backend el estado real y ya calculado de ESE
      // paciente puntual, en vez de tratar de derivarlo nosotros del
      // contenido del evento. Es un fetch chico (un solo paciente), y
      // es la única forma de estar seguros de que coincide con lo que
      // deteccion.py acaba de commitear.
      apiFetch(`/pacientes/${evento.paciente_id}`)
        .then((respuesta) => {
          if (!respuesta.ok) return null;
          return respuesta.json() as Promise<Paciente>;
        })
        .then((pacienteActualizado) => {
          if (!pacienteActualizado) return;
          setData((previos) =>
            previos.map((p) =>
              p.id === pacienteActualizado.id ? pacienteActualizado : p,
            ),
          );
        })
        .catch(() => {
          // Best-effort: si este fetch puntual falla, el paciente
          // simplemente se queda con el valor anterior hasta el
          // próximo evento -- no rompemos el resto del Dashboard por esto.
        });
    });
  }, [suscribir]);

  return { data, loading, error };
}

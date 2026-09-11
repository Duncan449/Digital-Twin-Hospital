import { useEffect, useState } from "react";
import type { SignoVital } from "../types/clinico";
import { apiFetch } from "../services/apiFetch";
import { useEventosWebSocket } from "../context/EventosWebSocketContext";

interface UseSignosVitalesResultado {
  data: SignoVital[];
  loading: boolean;
  error: string | null;
}

export function useSignosVitales(
  pacienteId: string,
): UseSignosVitalesResultado {
  const [data, setData] = useState<SignoVital[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { suscribir } = useEventosWebSocket();

  useEffect(() => {
    const controlador = new AbortController();

    async function cargarSignosVitales() {
      setLoading(true);
      setError(null);
      setData([]); // limpiamos el historial del paciente anterior al cambiar de id

      try {
        const respuesta = await apiFetch(
          `/pacientes/${pacienteId}/signos-vitales`,
          { signal: controlador.signal },
        );

        if (!respuesta.ok) {
          throw new Error(
            `El servidor respondió con estado ${respuesta.status}`,
          );
        }

        const json: SignoVital[] = await respuesta.json();
        setData(json);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        setError("No se pudo cargar el historial de signos vitales.");
      } finally {
        setLoading(false);
      }
    }

    cargarSignosVitales();

    return () => controlador.abort();
  }, [pacienteId]);

  // El canal WS ahora es GLOBAL (un solo socket para toda la
  // app, ver EventosWebSocketContext), así que acá filtramos por
  // paciente_id -- sin este chequeo, una medición de otro paciente
  // terminaría metida en este historial.
  useEffect(() => {
    return suscribir((evento) => {
      if (evento.tipo !== "medicion_registrada") return;
      if (evento.paciente_id !== pacienteId) return;

      const datos = evento.data;
      // El payload no trae un "id" propio de la medición (no hace
      // falta para mostrarla), así que generamos uno solo para
      // satisfacer el tipo SignoVital y darle a React una key estable.
      const nuevaMedicion: SignoVital = {
        id: crypto.randomUUID(),
        paciente_id: evento.paciente_id,
        tipo_signo_id: datos.tipo_signo_id as string,
        valor: datos.valor as string,
        // El evento no distingue el origen real (simulado/joystick/
        // manual) -- el historial completo que trae el fetch inicial
        // sí lo tiene bien, esto es solo una aproximación cosmética
        // para las mediciones que llegan en vivo.
        origen: "simulado",
        medido_en: datos.medido_en as string,
      };

      // El backend devuelve el historial DESC (más reciente primero);
      // mantenemos el mismo orden acá agregando al principio.
      setData((previas) => [nuevaMedicion, ...previas]);
    });
  }, [suscribir, pacienteId]);

  return { data, loading, error };
}

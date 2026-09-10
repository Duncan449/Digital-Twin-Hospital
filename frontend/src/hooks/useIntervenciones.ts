import { useState } from "react";
import type {
  IntervencionCrear,
  IntervencionRespuesta,
} from "../types/intervencion";
import { apiFetch } from "../services/apiFetch";

// Genera una respuesta con el mismo shape que devolvería el backend real
function generarMock(
  alertaId: string,
  datos: IntervencionCrear,
): IntervencionRespuesta {
  const ahora = new Date().toISOString();
  return {
    id: crypto.randomUUID(),
    alerta_id: alertaId,
    usuario_id: crypto.randomUUID(),
    accion: datos.accion,
    observaciones: datos.observaciones,
    iniciada_en: ahora,
    finalizada_en: ahora,
  };
}

interface UseIntervencionesResultado {
  enviarIntervencion: (
    alertaId: string,
    datos: IntervencionCrear,
  ) => Promise<IntervencionRespuesta | null>;
  enviando: boolean;
  error: string | null;
}

// A diferencia de useAlertas/useEventos (hooks de LECTURA que cargan
// solos al montar), este es un hook de ESCRITURA: no expone {data},
// expone una función para disparar la acción cuando el usuario confirma
// el formulario, más el estado de esa acción puntual (enviando/error).
export function useIntervenciones(): UseIntervencionesResultado {
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function enviarIntervencion(
    alertaId: string,
    datos: IntervencionCrear,
  ): Promise<IntervencionRespuesta | null> {
    setEnviando(true);
    setError(null);
    try {
      // --- MOCK (activo) ---
      await new Promise((resolve) => setTimeout(resolve, 400));
      if (!datos.accion.trim()) {
        throw new Error("La acción tomada es obligatoria.");
      }
      return generarMock(alertaId, datos);

      // --- FETCH REAL (Fase 4: descomentar, borrar el bloque MOCK de arriba) ---
      // apiFetch ya antepone API_URL y agrega el header Authorization.
      // const respuesta = await apiFetch(`/alertas/${alertaId}/intervenciones`, {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify(datos),
      // });
      // if (!respuesta.ok) {
      //   throw new Error("No se pudo registrar la intervención.");
      // }
      // return (await respuesta.json()) as IntervencionRespuesta;
    } catch (err) {
      const mensaje =
        err instanceof Error
          ? err.message
          : "Error desconocido al registrar la intervención.";
      setError(mensaje);
      return null;
    } finally {
      setEnviando(false);
    }
  }

  return { enviarIntervencion, enviando, error };
}

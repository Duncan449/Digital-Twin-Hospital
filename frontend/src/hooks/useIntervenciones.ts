import { useState } from "react";
import type {
  IntervencionCrear,
  IntervencionRespuesta,
} from "../types/intervencion";
import { apiFetch } from "../services/apiFetch";

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
      // El schema Pydantic (accion: str) NO rechaza un string vacío --
      // Pydantic v2 no valida "no vacío" salvo min_length explícito.
      // Esta validación es la única barrera real contra una
      // intervención sin acción, y hay que conservarla del lado del
      // cliente aunque IntervencionModal ya deshabilite el botón en
      // ese caso (defensa en profundidad: este hook podría reusarse
      // en otro componente que no tenga ese mismo chequeo).
      if (!datos.accion.trim()) {
        throw new Error("La acción tomada es obligatoria.");
      }

      const respuesta = await apiFetch(`/alertas/${alertaId}/intervenciones`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos),
      });

      if (!respuesta.ok) {
        throw new Error("No se pudo registrar la intervención.");
      }

      return (await respuesta.json()) as IntervencionRespuesta;
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

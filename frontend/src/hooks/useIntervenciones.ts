import { useState } from "react";
import type {
  IntervencionCrear,
  IntervencionRespuesta,
} from "../types/intervencion";
import { apiFetch } from "../services/apiFetch";

// Lógica pura de UNA llamada, sin tocar estado de React. La reusan tanto
// enviarIntervencion (una alerta) como enviarIntervencionATodas (N alertas
// en paralelo), para no duplicar este bloque en dos lugares.
//
// Validamos "accion" vacío ACÁ (client-side) porque el schema Pydantic
// IntervencionCrear (accion: str) no rechaza string vacío del lado del
// backend -- sin este chequeo, un POST con accion="" pasaría igual.
async function intentarIntervencion(
  alertaId: string,
  datos: IntervencionCrear,
): Promise<IntervencionRespuesta> {
  if (!datos.accion.trim()) {
    throw new Error("La acción tomada es obligatoria.");
  }

  const respuesta = await apiFetch(`/alertas/${alertaId}/intervenciones`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  });

  if (!respuesta.ok) {
    if (respuesta.status === 409) {
      throw new Error("Esta alerta ya fue resuelta por otra intervención.");
    }
    throw new Error(
      `No se pudo registrar la intervención para la alerta ${alertaId}.`,
    );
  }

  return (await respuesta.json()) as IntervencionRespuesta;
}

export interface ResultadoIntervencionMultiple {
  exitosas: IntervencionRespuesta[];
  fallidas: string[]; // ids de alerta que no se pudieron resolver
}

interface UseIntervencionesResultado {
  enviarIntervencion: (
    alertaId: string,
    datos: IntervencionCrear,
  ) => Promise<IntervencionRespuesta | null>;
  enviarIntervencionATodas: (
    alertaIds: string[],
    datos: IntervencionCrear,
  ) => Promise<ResultadoIntervencionMultiple>;
  enviando: boolean;
  error: string | null;
}

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
      return await intentarIntervencion(alertaId, datos);
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

  // Dispara una intervención por cada alerta activa del paciente, en
  // paralelo. No es atómico entre alertas -- cada POST es independiente,
  // igual que ya son independientes las alertas en el backend -- por eso
  // se reportan éxitos y fallos por separado en vez de todo-o-nada.
  async function enviarIntervencionATodas(
    alertaIds: string[],
    datos: IntervencionCrear,
  ): Promise<ResultadoIntervencionMultiple> {
    setEnviando(true);
    setError(null);

    const resultados = await Promise.allSettled(
      alertaIds.map((alertaId) => intentarIntervencion(alertaId, datos)),
    );

    const exitosas: IntervencionRespuesta[] = [];
    const fallidas: string[] = [];

    resultados.forEach((resultado, indice) => {
      if (resultado.status === "fulfilled") {
        exitosas.push(resultado.value);
      } else {
        fallidas.push(alertaIds[indice]);
      }
    });

    if (fallidas.length > 0) {
      setError(
        exitosas.length > 0
          ? `Se registraron ${exitosas.length} de ${alertaIds.length} intervenciones. ${fallidas.length} no se pudieron guardar.`
          : "No se pudo registrar ninguna intervención.",
      );
    }

    setEnviando(false);
    return { exitosas, fallidas };
  }

  return { enviarIntervencion, enviarIntervencionATodas, enviando, error };
}

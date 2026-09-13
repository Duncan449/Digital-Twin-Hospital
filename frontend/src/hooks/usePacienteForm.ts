import { useState } from "react";
import type {
  Paciente,
  PacienteActualizar,
  PacienteCrear,
} from "../types/pacientes";
import { apiFetch } from "../services/apiFetch";

interface UsePacienteFormResultado {
  crearPaciente: (datos: PacienteCrear) => Promise<Paciente | null>;
  actualizarPaciente: (
    pacienteId: string,
    datos: PacienteActualizar,
  ) => Promise<Paciente | null>;
  darDeAltaPaciente: (pacienteId: string) => Promise<Paciente | null>;
  enviando: boolean;
  error: string | null;
}

// Hook de ESCRITURA (mismo patrón que useIntervenciones): no expone
// {data}, expone funciones que disparan cada acción del CRUD de
// pacientes más el estado de esa acción puntual (enviando/error).
// Las tres acciones comparten el mismo estado enviando/error porque
// PacienteFormModal solo dispara una a la vez.
export function usePacienteForm(): UsePacienteFormResultado {
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function manejarRespuesta(
    respuesta: Response,
    mensajeError: string,
  ): Promise<Paciente | null> {
    if (!respuesta.ok) {
      // El backend manda 409 con detail cuando el documento ya existe
      // (o el paciente ya fue dado de alta) -- lo mostramos tal cual
      // en vez de un mensaje genérico, porque es información accionable
      // para quien está llenando el formulario.
      if (respuesta.status === 409) {
        const cuerpo = await respuesta.json();
        throw new Error(cuerpo.detail ?? mensajeError);
      }
      throw new Error(mensajeError);
    }
    return (await respuesta.json()) as Paciente;
  }

  async function crearPaciente(datos: PacienteCrear): Promise<Paciente | null> {
    setEnviando(true);
    setError(null);
    try {
      const respuesta = await apiFetch("/pacientes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos),
      });
      return await manejarRespuesta(respuesta, "No se pudo crear el paciente.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido.");
      return null;
    } finally {
      setEnviando(false);
    }
  }

  async function actualizarPaciente(
    pacienteId: string,
    datos: PacienteActualizar,
  ): Promise<Paciente | null> {
    setEnviando(true);
    setError(null);
    try {
      const respuesta = await apiFetch(`/pacientes/${pacienteId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos),
      });
      return await manejarRespuesta(
        respuesta,
        "No se pudo actualizar el paciente.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido.");
      return null;
    } finally {
      setEnviando(false);
    }
  }

  async function darDeAltaPaciente(
    pacienteId: string,
  ): Promise<Paciente | null> {
    setEnviando(true);
    setError(null);
    try {
      const respuesta = await apiFetch(`/pacientes/${pacienteId}/dar-de-alta`, {
        method: "PATCH",
      });
      return await manejarRespuesta(
        respuesta,
        "No se pudo dar de alta al paciente.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido.");
      return null;
    } finally {
      setEnviando(false);
    }
  }

  return {
    crearPaciente,
    actualizarPaciente,
    darDeAltaPaciente,
    enviando,
    error,
  };
}

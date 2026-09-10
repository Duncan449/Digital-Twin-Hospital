import { API_URL, CLAVE_TOKEN } from "./config";

// Wrapper para cualquier fetch que necesite ir autenticado. Pensado
// para Fase 4: cuando los hooks (usePacientes, useAlertas, etc.)
// reemplacen el mock por el fetch real ya escrito y comentado adentro,
// van a llamar a esto en vez de fetch() directo -- así ningún hook
// tiene que acordarse de armar el header a mano ni de manejar un 401
// por su cuenta.
export async function apiFetch(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const token = localStorage.getItem(CLAVE_TOKEN);

  const headers = new Headers(options.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const respuesta = await fetch(`${API_URL}${path}`, { ...options, headers });

  // Un 401 acá significa que el token guardado ya no sirve (expiró o el
  // backend lo rechazó). No tiene sentido que cada hook decida qué
  // hacer por su cuenta: cortamos la sesión en un solo lugar.
  if (respuesta.status === 401) {
    localStorage.removeItem(CLAVE_TOKEN);
    window.location.href = "/login";
  }

  return respuesta;
}

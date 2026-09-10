import { API_URL } from "./config";

interface RespuestaToken {
  access_token: string;
  token_type: string;
}

// Distinguimos DOS familias de error para que Login.tsx pueda mostrar
// un mensaje correcto en cada caso, en vez de "credenciales incorrectas"
// para todo (que fue justo lo que confundió con el bug de CORS).
export class ErrorDeRed extends Error {}
export class ErrorCredenciales extends Error {}

// El backend espera x-www-form-urlencoded porque /auth/login usa
// OAuth2PasswordRequestForm (el mismo estándar que usa el botón
// "Authorize" de Swagger) -- no es JSON como el resto de la API.
// El campo se llama "username" aunque mandemos el email: así lo pide
// ese estándar, form_data.username lo recibe el backend igual.
export async function iniciarSesion(
  email: string,
  password: string,
): Promise<RespuestaToken> {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  let respuesta: Response;
  try {
    respuesta = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
  } catch {
    // fetch() tira una excepción ACÁ cuando ni siquiera pudo completar
    // el request: servidor caído, sin conexión, o el navegador bloqueó
    // la respuesta por CORS. En ningún caso llegamos a ver un status
    // code -- por eso es un catch aparte, antes de mirar respuesta.ok.
    throw new ErrorDeRed(
      "No se pudo conectar con el servidor. Verificá tu conexión.",
    );
  }

  if (!respuesta.ok) {
    // Acá el backend SÍ respondió (no es problema de red): un 401 o 403
    // real de autenticar_usuario() en usuarios_service.py.
    throw new ErrorCredenciales("Email o contraseña incorrectos.");
  }

  return respuesta.json();
}

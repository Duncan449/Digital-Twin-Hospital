import { API_URL } from "./config";

interface RespuestaToken {
  access_token: string;
  token_type: string;
}

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

  const respuesta = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  if (!respuesta.ok) {
    throw new Error("Email o contraseña incorrectos.");
  }

  return respuesta.json();
}
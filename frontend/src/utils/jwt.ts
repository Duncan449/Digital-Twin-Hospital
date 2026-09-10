interface PayloadToken {
  sub: string;
  exp: number;
}

// Un JWT tiene 3 partes separadas por ".": header.payload.firma.
// La firma no la podemos verificar en el frontend (no tenemos la
// secret_key, y está bien que sea así, esa verificación es trabajo
// del backend). Acá solo decodificamos el payload para leer 'sub'
// (id de usuario) y 'exp' (expiración), sin otra llamada al backend.
export function decodificarToken(token: string): PayloadToken | null {
  try {
    const payloadBase64 = token.split(".")[1];
    // JWT usa base64url (- y _ en vez de + y /), hay que normalizarlo
    // antes de pasarlo a atob, que solo entiende base64 estándar.
    const normalizado = payloadBase64.replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(normalizado));
  } catch {
    return null;
  }
}
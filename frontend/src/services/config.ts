// Centraliza la URL base del backend. La va a
// reusar todo services/ a partir de acá, no solo auth.
export const API_URL = "http://localhost:8000";

// Mismo host y puerto que la API REST, pero con esquema ws://
// en vez de http://. Si el día de mañana el backend pasa a HTTPS
// (https://...), este mismo reemplazo produce wss:// automáticamente,
// sin tener que tocar esta línea.
export const WS_URL = API_URL.replace(/^http/, "ws");

// Misma clave que usa AuthContext para guardar el token en localStorage,
// centralizada acá para que AuthContext.tsx y apiFetch.ts no puedan
// desincronizarse si alguna vez cambia.
export const CLAVE_TOKEN = "dth_token";

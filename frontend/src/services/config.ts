// Centraliza la URL base del backend. La va a
// reusar todo services/ a partir de acá, no solo auth.
export const API_URL = "http://localhost:8000";

// Misma clave que usa AuthContext para guardar el token en localStorage,
// centralizada acá para que AuthContext.tsx y apiFetch.ts no puedan
// desincronizarse si alguna vez cambia.
export const CLAVE_TOKEN = "dth_token";

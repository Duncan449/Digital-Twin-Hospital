import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { decodificarToken } from "../utils/jwt";
import { iniciarSesion as iniciarSesionApi } from "../services/auth";

interface AuthContextValue {
  token: string | null;
  usuarioId: string | null;
  estaAutenticado: boolean;
  cargando: boolean;
  iniciarSesion: (email: string, password: string) => Promise<void>;
  cerrarSesion: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const CLAVE_STORAGE = "dth_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [usuarioId, setUsuarioId] = useState<string | null>(null);
  // 'cargando' evita que, en el primer render, ProtectedRoute mande a
  // /login antes de que terminemos de leer localStorage.
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const tokenGuardado = localStorage.getItem(CLAVE_STORAGE);
    if (tokenGuardado) {
      const payload = decodificarToken(tokenGuardado);
      // Si el token guardado ya expiró (recordá: son 30 min sin
      // refresh), lo descartamos acá en vez de dejar que el usuario
      // navegue con un token que el backend igual va a rechazar con 401.
      if (payload && payload.exp * 1000 > Date.now()) {
        setToken(tokenGuardado);
        setUsuarioId(payload.sub);
      } else {
        localStorage.removeItem(CLAVE_STORAGE);
      }
    }
    setCargando(false);
  }, []);

  async function iniciarSesion(email: string, password: string) {
    const { access_token } = await iniciarSesionApi(email, password);
    const payload = decodificarToken(access_token);
    localStorage.setItem(CLAVE_STORAGE, access_token);
    setToken(access_token);
    setUsuarioId(payload?.sub ?? null);
  }

  function cerrarSesion() {
    localStorage.removeItem(CLAVE_STORAGE);
    setToken(null);
    setUsuarioId(null);
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        usuarioId,
        estaAutenticado: !!token,
        cargando,
        iniciarSesion,
        cerrarSesion,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
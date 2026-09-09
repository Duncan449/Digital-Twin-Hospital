import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Reemplaza el <Outlet/> de las rutas que envuelve: si no hay sesión,
// redirige a /login en vez de renderizar la página pedida.
function ProtectedRoute() {
  const { estaAutenticado, cargando } = useAuth();

  if (cargando) return null; // evita el parpadeo hacia /login
  if (!estaAutenticado) return <Navigate to="/login" replace />;

  return <Outlet />;
}

export default ProtectedRoute;
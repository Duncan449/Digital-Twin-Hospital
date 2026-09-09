import { Link, Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Layout envuelve TODAS las páginas (Dashboard y Digital Twin) con el
// mismo header. <Outlet /> es el punto donde React Router inserta la
// página que corresponda según la URL -- es como un {children} pero
// manejado por el router en vez de pasado a mano.
function Layout() {
  // Reloj en tiempo real: es la hora del NAVEGADOR, no viene del backend
  // ni de ningún WebSocket -- se actualiza sola cada segundo, como un
  // reloj de pared. No hay que confundirlo con "WS LIVE" del mockup, que
  // sí dependería de la conexión real (eso queda para la Fase 5).
  const [hora, setHora] = useState(() => new Date());

  useEffect(() => {
    const intervalo = setInterval(() => setHora(new Date()), 1000);
    return () => clearInterval(intervalo);
  }, []);

  const { cerrarSesion } = useAuth();
  const navigate = useNavigate();

  function manejarLogout() {
    cerrarSesion();
    navigate("/login");
  }

  return (
    <div>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: "20px",
          padding: "14px 22px",
          borderBottom: "1px solid var(--border)",
          background: "var(--bg-panel-alt)",
        }}
      >
        <Link
          to="/"
          style={{
            display: "inline-flex",
            flexDirection: "column",
            lineHeight: 1.15,
            textDecoration: "none",
          }}
        >
          <span
            style={{
              fontSize: "15px",
              fontWeight: 700,
              letterSpacing: ".14em",
              color: "var(--text-h)",
            }}
          >
            VITA<span style={{ color: "var(--color-normal)" }}>·</span>TWIN
          </span>
          <span
            style={{
              fontFamily: "var(--mono)",
              fontSize: "9.5px",
              color: "var(--text-muted)",
              letterSpacing: ".12em",
              marginTop: "2px",
            }}
          >
            DIGITAL TWIN MONITORING
          </span>
        </Link>

        <span
          style={{
            marginLeft: "auto",
            fontFamily: "var(--mono)",
            fontSize: "15px",
            fontWeight: 600,
            color: "var(--text-h)",
            letterSpacing: ".06em",
          }}
        >
          {hora.toLocaleTimeString("es-AR")}
        </span>

        <button
          onClick={manejarLogout}
          style={{
            fontFamily: "var(--mono)",
            fontSize: "11px",
            letterSpacing: ".08em",
            color: "var(--text-muted)",
            background: "transparent",
            border: "1px solid var(--border)",
            borderRadius: "6px",
            padding: "6px 12px",
            cursor: "pointer",
          }}
        >
          CERRAR SESIÓN
        </button>
      </header>

      <main style={{ padding: "1rem" }}>
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;

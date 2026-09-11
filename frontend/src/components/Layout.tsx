import { Link, Outlet } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useEventosWebSocket } from "../context/EventosWebSocketContext";

// Layout envuelve TODAS las páginas (Dashboard y Digital Twin) con el
// mismo header. <Outlet /> es el punto donde React Router inserta la
// página que corresponda según la URL.
function Layout() {
  const [hora, setHora] = useState(() => new Date());
  // Diferencia (ms) entre la hora del servidor y la del navegador. Se
  // actualiza con el timestamp que trae CADA mensaje WS (ver
  // publicar_evento en el backend), no con un solo intercambio inicial.
  const desfaseRef = useRef(0);
  const { conectado, suscribir } = useEventosWebSocket();

  useEffect(() => {
    const intervalo = setInterval(() => {
      setHora(new Date(Date.now() + desfaseRef.current));
    }, 1000);
    return () => clearInterval(intervalo);
  }, []);

  // Cuando no llegan eventos por un rato, el reloj sigue andando solo
  // (el setInterval de arriba no depende de esto) -- este efecto solo
  // corrige el desfase cada vez que hay novedades desde el backend.
  useEffect(() => {
    return suscribir((evento) => {
      const horaServidor = new Date(evento.timestamp).getTime();
      desfaseRef.current = horaServidor - Date.now();
    });
  }, [suscribir]);

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
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            fontFamily: "var(--mono)",
            fontSize: "10px",
            letterSpacing: ".1em",
            color: conectado ? "var(--color-normal)" : "var(--text-muted)",
          }}
        >
          <span
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              background: conectado
                ? "var(--color-normal)"
                : "var(--text-muted)",
              boxShadow: conectado ? "0 0 8px var(--color-normal)" : "none",
            }}
          />
          {conectado ? "WS LIVE" : "SIN CONEXIÓN"}
        </span>

        <span
          style={{
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

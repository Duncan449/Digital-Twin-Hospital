import { Link, Outlet } from "react-router-dom";

// Layout envuelve TODAS las páginas (Dashboard y Digital Twin) con el
// mismo header. <Outlet /> es el punto donde React Router inserta la
// página que corresponda según la URL -- es como un {children} pero
// manejado por el router en vez de pasado a mano.
function Layout() {
  return (
    <div>
      <header
        style={{
          padding: "1rem",
          borderBottom: "1px solid #ccc",
        }}
      >
        <Link to="/" style={{ textDecoration: "none", fontWeight: "bold" }}>
          Digital Twin Hospital
        </Link>
      </header>

      <main style={{ padding: "1rem" }}>
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;

import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import DigitalTwinView from "./pages/DigitalTwinView";

// Layout envuelve a las dos páginas gracias al <Route element={<Layout />}>
// sin path propio -- eso significa "aplicá este layout a todas las rutas
// hijas", no "esta es una ruta más". Las rutas hijas se resuelven adentro
// del <Outlet /> de Layout.
function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/pacientes/:id" element={<DigitalTwinView />} />
      </Route>
    </Routes>
  );
}

export default App;

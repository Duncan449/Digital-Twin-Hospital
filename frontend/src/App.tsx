import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import DigitalTwinView from "./pages/DigitalTwinView";
import Login from "./pages/Login";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      {/* ProtectedRoute envuelve a Layout: si no hay sesión, ni
          siquiera se monta el header ni el Outlet de adentro. */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/pacientes/:id" element={<DigitalTwinView />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
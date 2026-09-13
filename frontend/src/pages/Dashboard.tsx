import { useState } from "react";
import { usePacientes } from "../hooks/usePacientes";
import { useAlertas } from "../hooks/useAlertas";
import { useTiposSignosVitales } from "../hooks/useTiposSignosVitales";
import PatientCard from "../components/PatientCard";
import AlertasActivas from "../components/AlertasActivas";
import KpiPanel from "../components/KpiPanel";
import PacienteFormModal from "../components/PacienteFormModal";
import type { Paciente } from "../types/pacientes";
import "./Dashboard.css";

function Dashboard() {
  const { data: pacientes, loading, error, recargar } = usePacientes();
  const { data: alertas } = useAlertas();
  const { data: tiposSignosVitales } = useTiposSignosVitales();

  const [modalAbierto, setModalAbierto] = useState(false);

  function manejarExitoCreacion(_resultado: Paciente) {
    setModalAbierto(false);
    // El backend ya creó el paciente; recargamos la lista en vez de
    // insertarlo a mano en el estado local, para que el resto de la
    // fila (digital_twin, fecha_ingreso, etc.) quede siempre en sync
    // con lo que realmente quedó guardado en la base.
    recargar();
  }

  if (loading) return <p>Cargando pacientes...</p>;
  if (error) return <p>Error: {error}</p>;

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <h1>Dashboard</h1>
        <button
          onClick={() => setModalAbierto(true)}
          style={{
            padding: "9px 16px",
            borderRadius: 9,
            border: "1px solid var(--color-normal)",
            background: "var(--tint-normal)",
            color: "var(--color-normal)",
            fontSize: 13,
            fontWeight: 700,
            cursor: "pointer",
            height: "fit-content",
          }}
        >
          + Nuevo paciente
        </button>
      </div>

      <AlertasActivas
        alertas={alertas}
        pacientes={pacientes}
        tiposSignosVitales={tiposSignosVitales}
      />
      <KpiPanel pacientes={pacientes} />
      <div className="dashboard-grid">
        {pacientes.map((paciente) => (
          <PatientCard
            key={paciente.id}
            paciente={paciente}
            tiposSignosVitales={tiposSignosVitales}
          />
        ))}
      </div>

      <PacienteFormModal
        abierto={modalAbierto}
        modo="crear"
        onCerrar={() => setModalAbierto(false)}
        onExito={manejarExitoCreacion}
      />
    </div>
  );
}

export default Dashboard;

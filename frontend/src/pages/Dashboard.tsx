import { usePacientes } from "../hooks/usePacientes";
import { useAlertas } from "../hooks/useAlertas";
import PatientCard from "../components/PatientCard";
import AlertasActivas from "../components/AlertasActivas";
import "./Dashboard.css";

function Dashboard() {
  const { data: pacientes, loading, error } = usePacientes();
  const { data: alertas } = useAlertas();

  if (loading) return <p>Cargando pacientes...</p>;
  if (error) return <p>Error: {error}</p>;

  return (
    <div>
      <h1>Dashboard</h1>
      <AlertasActivas alertas={alertas} pacientes={pacientes} />
      <div className="dashboard-grid">
        {pacientes.map((paciente) => (
          <PatientCard key={paciente.id} paciente={paciente} />
        ))}
      </div>
    </div>
  );
}

export default Dashboard;

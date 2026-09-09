import { Link } from "react-router-dom";
import { usePacientes } from "../hooks/usePacientes";

// Todavía sin estilos ni PatientCard -- eso es Fase 2. Acá el objetivo
// único es probar que la navegación funciona: click en un paciente
// tiene que llevarte a /pacientes/:id con el id correcto.
function Dashboard() {
  const { data: pacientes, loading, error } = usePacientes();

  if (loading) return <p>Cargando pacientes...</p>;
  if (error) return <p>Error: {error}</p>;

  return (
    <div>
      <h1>Dashboard</h1>
      <ul>
        {pacientes.map((paciente) => (
          <li key={paciente.id}>
            <Link to={`/pacientes/${paciente.id}`}>
              {paciente.nombre} {paciente.apellido} — sala{" "}
              {paciente.sala ?? "sin asignar"} (
              {paciente.digital_twin.severidad_actual})
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Dashboard;

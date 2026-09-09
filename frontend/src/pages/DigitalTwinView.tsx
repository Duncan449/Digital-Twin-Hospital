import { useParams } from "react-router-dom";
import { usePaciente } from "../hooks/usePaciente";
import { useSignosVitales } from "../hooks/useSignosVitales";

// useParams() lee los segmentos dinámicos de la URL. Como la ruta está
// definida como "/pacientes/:id" en App.tsx, entrar a
// "/pacientes/a1b2c3d4-...-0001" hace que params.id sea exactamente ese
// string -- ya no hace falta el ID_PACIENTE_DE_PRUEBA hardcodeado.
function DigitalTwinView() {
  const { id } = useParams<{ id: string }>();

  const paciente = usePaciente(id ?? "");
  const signosVitales = useSignosVitales(id ?? "");

  if (paciente.loading) return <p>Cargando paciente...</p>;
  if (paciente.error) return <p>Error: {paciente.error}</p>;
  if (!paciente.data) return null;

  return (
    <div>
      <h1>
        {paciente.data.nombre} {paciente.data.apellido}
      </h1>
      <p>
        Sala: {paciente.data.sala ?? "sin asignar"} — Cama:{" "}
        {paciente.data.cama ?? "-"}
      </p>
      <p>Severidad actual: {paciente.data.digital_twin.severidad_actual}</p>

      <h2>Historial de signos vitales ({signosVitales.data.length})</h2>
      {signosVitales.loading && <p>Cargando mediciones...</p>}
      <pre>{JSON.stringify(signosVitales.data, null, 2)}</pre>
    </div>
  );
}

export default DigitalTwinView;

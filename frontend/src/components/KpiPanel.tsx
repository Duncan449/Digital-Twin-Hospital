import type { Paciente } from "../types/pacientes";

interface KpiPanelProps {
  pacientes: Paciente[];
}

interface Kpi {
  etiqueta: string;
  valor: number;
  sub: string;
  color: string;
}

function KpiPanel({ pacientes }: KpiPanelProps) {
  // Los "dados de alta" no cuentan para ningún KPI: ya no están bajo
  // monitoreo, así que ni suman a "activos" ni a ningún balde de severidad.
  const activos = pacientes.filter((p) => p.estado === "internado");
  const criticos = activos.filter(
    (p) => p.digital_twin.severidad_actual === "critica",
  ).length;
  const precaucion = activos.filter(
    (p) => p.digital_twin.severidad_actual === "precaucion",
  ).length;
  const estables = activos.filter(
    (p) => p.digital_twin.severidad_actual === "normal",
  ).length;

  const kpis: Kpi[] = [
    {
      etiqueta: "PACIENTES ACTIVOS",
      valor: activos.length,
      sub: `En total`,
      color: "var(--accent)",
    },
    {
      etiqueta: "CRÍTICOS",
      valor: criticos,
      sub: "intervención",
      color: "var(--color-critica)",
    },
    {
      etiqueta: "PRECAUCIÓN",
      valor: precaucion,
      sub: "vigilancia",
      color: "var(--color-precaucion)",
    },
    {
      etiqueta: "ESTABLES",
      valor: estables,
      sub: "en rango",
      color: "var(--color-normal)",
    },
  ];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
        gap: "12px",
        marginBottom: "22px",
      }}
    >
      {kpis.map((kpi) => (
        <div
          key={kpi.etiqueta}
          style={{
            padding: "14px 16px",
            borderRadius: "12px",
            background: "var(--bg-panel-alt)",
            border: "1px solid var(--border)",
            borderLeft: `3px solid ${kpi.color}`,
          }}
        >
          <div
            style={{
              fontFamily: "var(--mono)",
              fontSize: "10px",
              letterSpacing: ".16em",
              color: "var(--text-muted)",
            }}
          >
            {kpi.etiqueta}
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "baseline",
              gap: "8px",
              marginTop: "6px",
            }}
          >
            <span
              style={{
                fontFamily: "var(--mono)",
                fontSize: "28px",
                fontWeight: 600,
                color: kpi.color,
              }}
            >
              {kpi.valor}
            </span>
            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              {kpi.sub}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default KpiPanel;

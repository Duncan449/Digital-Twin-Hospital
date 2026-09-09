// frontend/src/components/VitalSignChart.tsx
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { SignoVital, TipoSignoVital } from "../types/clinico";

interface VitalSignChartProps {
  tipo: TipoSignoVital;
  historial: SignoVital[]; // ya filtrado por tipo, orden ascendente por medido_en
}

const formateaHora = (iso: string) =>
  new Date(iso).toLocaleTimeString("es-AR", {
    hour: "2-digit",
    minute: "2-digit",
  });

function VitalSignChart({ tipo, historial }: VitalSignChartProps) {
  const datos = historial.map((s) => ({
    hora: formateaHora(s.medido_en),
    valor: s.valor,
  }));

  return (
    <div
      style={{
        padding: 16,
        borderRadius: 14,
        background: "#0B1423",
        border: "1px solid #1A2740",
      }}
    >
      <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 2 }}>
        {tipo.nombre}
      </div>
      <div
        style={{
          fontFamily: "'IBM Plex Mono', monospace",
          fontSize: 10,
          letterSpacing: "0.12em",
          color: "#5C7292",
          marginBottom: 12,
        }}
      >
        EVOLUCIÓN · {tipo.unidad.toUpperCase()}
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart
          data={datos}
          margin={{ top: 5, right: 10, left: -10, bottom: 0 }}
        >
          {/* Franja verde = rango normal, para ver de un vistazo cuándo la línea se sale */}
          <ReferenceArea
            y1={tipo.rango_normal_min}
            y2={tipo.rango_normal_max}
            fill="#10B981"
            fillOpacity={0.08}
          />
          <XAxis
            dataKey="hora"
            stroke="#3E5271"
            tick={{ fontSize: 10, fontFamily: "'IBM Plex Mono', monospace" }}
          />
          <YAxis
            domain={[tipo.rango_critico_min, tipo.rango_critico_max]}
            stroke="#3E5271"
            tick={{ fontSize: 10, fontFamily: "'IBM Plex Mono', monospace" }}
            width={38}
          />
          <Tooltip
            contentStyle={{
              background: "#0C1524",
              border: "1px solid #24344F",
              borderRadius: 8,
              fontSize: 12,
            }}
            labelStyle={{ color: "#8FA6C4" }}
          />
          <Line
            type="monotone"
            dataKey="valor"
            stroke="#38BDF8"
            strokeWidth={2}
            dot={{ r: 2 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default VitalSignChart;

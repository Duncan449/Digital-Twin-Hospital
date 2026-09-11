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

// Para los TICKS del eje: alcanza con hora:minuto, 
// no hace falta más precisión ahí.
const formateaTick = (timestampMs: number) =>
  new Date(timestampMs).toLocaleTimeString("es-AR", {
    hour: "2-digit",
    minute: "2-digit",
  });

// Para el TOOLTIP (un solo punto bajo el cursor): acá sí
// necesitamos los segundos -- es lo que permite distinguir mediciones
// que caen dentro del mismo minuto (típico durante una simulación con
// intervalo_segundos chico, donde puede haber varias mediciones en los
// mismos 60 segundos).
const formateaTooltip = (timestampMs: number) =>
  new Date(timestampMs).toLocaleTimeString("es-AR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

function VitalSignChart({ tipo, historial }: VitalSignChartProps) {
  // Eje X NUMÉRICO, no un string categórico: con un eje de
  // tipo "category" (el default de Recharts si dataKey es un string),
  // Recharts posiciona los puntos por ÍNDICE en el array, no por su
  // valor real. Si dos mediciones caen en el mismo minuto, comparten
  // la misma etiqueta de texto y terminan amontonadas visualmente, y el
  // tooltip termina enganchando el punto más cercano por índice en vez
  // del que está realmente bajo el cursor. Con un eje numérico basado
  // en el timestamp real, cada punto tiene su posición exacta y
  // proporcional al tiempo transcurrido -- sin colisiones posibles.
  const datos = historial.map((s) => ({
    tiempo: new Date(s.medido_en).getTime(),
    valor: Number(s.valor),
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
            dataKey="tiempo"
            type="number"
            domain={["dataMin", "dataMax"]}
            tickFormatter={formateaTick}
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
            labelFormatter={(valor) => formateaTooltip(valor as number)}
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

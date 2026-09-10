interface SparklineProps {
  valores: number[]; // orden cronológico ascendente
  color: string;
}

function Sparkline({ valores, color }: SparklineProps) {
  if (valores.length < 2) {
    return (
      <div
        style={{
          height: 46,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 11,
          color: "var(--text-muted)",
        }}
      >
        Sin historial suficiente
      </div>
    );
  }

  const minimo = Math.min(...valores);
  const maximo = Math.max(...valores);
  const rango = maximo - minimo || 1; // evita dividir por cero si todos los valores son iguales

  const puntos = valores
    .map((v, i) => {
      const x = (i / (valores.length - 1)) * 240;
      const y = 44 - ((v - minimo) / rango) * 40;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg
      viewBox="0 0 240 46"
      preserveAspectRatio="none"
      style={{ width: "100%", height: 46, display: "block" }}
    >
      <polyline
        points={puntos}
        fill="none"
        stroke={color}
        strokeWidth={1.6}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default Sparkline;

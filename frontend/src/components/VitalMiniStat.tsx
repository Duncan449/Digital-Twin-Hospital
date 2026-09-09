interface VitalMiniStatProps {
  etiqueta: string;
  valor: string;
  unidad: string;
  color: string;
}

function VitalMiniStat({ etiqueta, valor, unidad, color }: VitalMiniStatProps) {
  return (
    <div
      style={{
        padding: "9px 10px",
        borderRadius: "9px",
        background: "var(--bg)",
        border: "1px solid var(--border-subtle)",
      }}
    >
      <div
        style={{
          fontFamily: "var(--mono)",
          fontSize: "8.5px",
          letterSpacing: ".12em",
          color: "var(--text-muted)",
        }}
      >
        {etiqueta}
      </div>
      <div
        style={{
          fontFamily: "var(--mono)",
          fontSize: "19px",
          fontWeight: 600,
          color,
        }}
      >
        {valor}
      </div>
      <div
        style={{
          fontFamily: "var(--mono)",
          fontSize: "8.5px",
          color: "var(--text-muted)",
        }}
      >
        {unidad}
      </div>
    </div>
  );
}

export default VitalMiniStat;

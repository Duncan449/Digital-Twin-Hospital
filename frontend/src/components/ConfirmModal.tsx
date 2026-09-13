interface ConfirmModalProps {
  abierto: boolean;
  titulo: string;
  mensaje: string;
  textoAceptar?: string;
  textoCancelar?: string;
  // Colores del botón de aceptar: por default "peligro" (rojo/crítico),
  // pero "alta" para acciones como dar de alta, que no son un error
  // sino un cambio de estado neutro.
  variante?: "peligro" | "alta";
  procesando?: boolean;
  onAceptar: () => void;
  onCancelar: () => void;
}

const COLORES_VARIANTE = {
  peligro: {
    color: "var(--color-critica)",
    tint: "var(--tint-critica)",
    border: "var(--border-critica)",
  },
  alta: {
    color: "var(--color-alta)",
    tint: "var(--tint-alta)",
    border: "var(--border-alta)",
  },
};

// Reemplaza a window.confirm() para cualquier acción que necesite una
// confirmación simple de sí/no: no tiene campos, solo un mensaje y dos
// botones. Para acciones con formulario (varios campos) usar un modal
// dedicado como PacienteFormModal, no este.
function ConfirmModal({
  abierto,
  titulo,
  mensaje,
  textoAceptar = "Aceptar",
  textoCancelar = "Cancelar",
  variante = "peligro",
  procesando = false,
  onAceptar,
  onCancelar,
}: ConfirmModalProps) {
  if (!abierto) return null;

  const estilo = COLORES_VARIANTE[variante];

  return (
    <div
      onClick={onCancelar}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(3, 6, 12, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1100,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 400,
          maxWidth: "90vw",
          background: "var(--bg-panel)",
          border: `1px solid ${estilo.border}`,
          borderRadius: 14,
          boxShadow: `0 0 40px ${estilo.tint}`,
          padding: 22,
          fontFamily: "var(--sans)",
          color: "var(--text-h)",
        }}
      >
        <h2 style={{ margin: "0 0 10px", fontSize: 16.5, fontWeight: 700 }}>
          {titulo}
        </h2>
        <p
          style={{
            margin: "0 0 20px",
            fontSize: 13.5,
            lineHeight: 1.5,
            color: "var(--text-muted)",
          }}
        >
          {mensaje}
        </p>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
          <button
            onClick={onCancelar}
            disabled={procesando}
            style={{
              padding: "10px 18px",
              borderRadius: 8,
              fontFamily: "var(--sans)",
              fontWeight: 600,
              fontSize: 13.5,
              cursor: procesando ? "not-allowed" : "pointer",
              opacity: procesando ? 0.5 : 1,
              background: "transparent",
              border: "1px solid var(--border)",
              color: "var(--text-h)",
            }}
          >
            {textoCancelar}
          </button>
          <button
            onClick={onAceptar}
            disabled={procesando}
            style={{
              padding: "10px 18px",
              borderRadius: 8,
              fontFamily: "var(--sans)",
              fontWeight: 700,
              fontSize: 13.5,
              cursor: procesando ? "not-allowed" : "pointer",
              opacity: procesando ? 0.6 : 1,
              background: estilo.tint,
              border: `1px solid ${estilo.border}`,
              color: estilo.color,
            }}
          >
            {procesando ? "Procesando..." : textoAceptar}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmModal;
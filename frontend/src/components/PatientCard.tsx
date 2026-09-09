import { Link } from "react-router-dom";
import type { Paciente } from "../types/pacientes";
import type { NivelSeveridad } from "../types/enums";
import type { SignoVital, TipoSignoVital } from "../types/clinico";
import { useSignosVitales } from "../hooks/useSignosVitales";
import { calcularSeveridadSigno } from "../utils/severidadSigno";
import { COLOR_SEVERIDAD } from "../constants/severidad";
import Sparkline from "./Sparkline";
import VitalMiniStat from "./VitalMiniStat";

interface PatientCardProps {
  paciente: Paciente;
  tiposSignosVitales: TipoSignoVital[];
}

type EstiloTarjeta = {
  color: string;
  tint: string;
  border: string;
  label: string;
};

const ESTILO_POR_SEVERIDAD: Record<NivelSeveridad, EstiloTarjeta> = {
  normal: {
    color: "var(--color-normal)",
    tint: "var(--tint-normal)",
    border: "var(--border-normal)",
    label: "ESTABLE",
  },
  precaucion: {
    color: "var(--color-precaucion)",
    tint: "var(--tint-precaucion)",
    border: "var(--border-precaucion)",
    label: "PRECAUCIÓN",
  },
  critica: {
    color: "var(--color-critica)",
    tint: "var(--tint-critica)",
    border: "var(--border-critica)",
    label: "CRÍTICO",
  },
};

const ESTILO_DADO_DE_ALTA: EstiloTarjeta = {
  color: "var(--color-alta)",
  tint: "var(--tint-alta)",
  border: "var(--border-alta)",
  label: "DADO DE ALTA",
};

// Busca la medición más reciente de un tipo puntual dentro del
// historial completo del paciente (que trae TODOS los tipos mezclados).
function obtenerUltimoValor(
  historial: SignoVital[],
  tipoId: string | undefined,
): SignoVital | undefined {
  if (tipoId === undefined) return undefined;
  const filtrado = historial.filter((s) => s.tipo_signo_id === tipoId);
  if (filtrado.length === 0) return undefined;
  return filtrado.reduce((masReciente, actual) =>
    actual.medido_en > masReciente.medido_en ? actual : masReciente,
  );
}

function PatientCard({ paciente, tiposSignosVitales }: PatientCardProps) {
  const estaDadoDeAlta = paciente.estado === "dado_de_alta";

  const estilo = estaDadoDeAlta
    ? ESTILO_DADO_DE_ALTA
    : ESTILO_POR_SEVERIDAD[paciente.digital_twin.severidad_actual];

  const esCritica =
    !estaDadoDeAlta && paciente.digital_twin.severidad_actual === "critica";

  // Un solo fetch por card (historial completo del paciente, todos los
  // tipos); de ahí sacamos tanto el sparkline de FC como las 3 mini
  // tarjetas -- no hace falta pedir nada más de una vez.
  const signosVitales = useSignosVitales(paciente.id);

  const tipoFc = tiposSignosVitales.find(
    (t) => t.nombre === "Frecuencia cardíaca",
  );
  const tipoSpo2 = tiposSignosVitales.find(
    (t) => t.nombre === "Saturación de oxígeno",
  );
  const tipoSistolica = tiposSignosVitales.find(
    (t) => t.nombre === "Presión sistólica",
  );
  const tipoDiastolica = tiposSignosVitales.find(
    (t) => t.nombre === "Presión diastólica",
  );

  const historialFc = signosVitales.data
    .filter((s) => s.tipo_signo_id === tipoFc?.id)
    .slice()
    .sort((a, b) => (a.medido_en < b.medido_en ? -1 : 1))
    .map((s) => Number(s.valor));

  const ultimaFc = obtenerUltimoValor(signosVitales.data, tipoFc?.id);
  const ultimaSpo2 = obtenerUltimoValor(signosVitales.data, tipoSpo2?.id);
  const ultimaSistolica = obtenerUltimoValor(
    signosVitales.data,
    tipoSistolica?.id,
  );
  const ultimaDiastolica = obtenerUltimoValor(
    signosVitales.data,
    tipoDiastolica?.id,
  );

  const colorFc =
    tipoFc && ultimaFc
      ? COLOR_SEVERIDAD[calcularSeveridadSigno(Number(ultimaFc.valor), tipoFc)]
      : "var(--text-muted)";
  const colorSpo2 =
    tipoSpo2 && ultimaSpo2
      ? COLOR_SEVERIDAD[
          calcularSeveridadSigno(Number(ultimaSpo2.valor), tipoSpo2)
        ]
      : "var(--text-muted)";
  const colorBp =
    tipoSistolica && ultimaSistolica
      ? COLOR_SEVERIDAD[
          calcularSeveridadSigno(Number(ultimaSistolica.valor), tipoSistolica)
        ]
      : "var(--text-muted)";

  const bpTexto = `${ultimaSistolica ? Number(ultimaSistolica.valor) : "–"}/${ultimaDiastolica ? Number(ultimaDiastolica.valor) : "–"}`;

  return (
    <Link
      to={`/pacientes/${paciente.id}`}
      style={{
        position: "relative",
        display: "block",
        textDecoration: "none",
        color: "inherit",
        padding: "17px 17px 17px 20px",
        borderRadius: "14px",
        background:
          "linear-gradient(165deg, var(--bg-panel), var(--bg-panel-alt))",
        border: `1px solid ${estilo.border}`,
        boxShadow: `0 0 0 1px rgba(0,0,0,.4), 0 0 22px ${estilo.tint}`,
        opacity: estaDadoDeAlta ? 0.55 : 1,
      }}
    >
      <span
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: "3px",
          borderRadius: "14px 0 0 14px",
          background: estilo.color,
          boxShadow: `0 0 10px ${estilo.color}`,
          animation: esCritica
            ? "critblink 1.1s ease-in-out infinite"
            : undefined,
        }}
      />

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "10px",
        }}
      >
        <strong style={{ fontSize: "15px", color: "var(--text-h)" }}>
          {paciente.nombre} {paciente.apellido}
        </strong>
        <span
          style={{
            padding: "4px 9px",
            borderRadius: "6px",
            fontFamily: "var(--mono)",
            fontSize: "9.5px",
            letterSpacing: ".14em",
            fontWeight: 600,
            color: estilo.color,
            background: estilo.tint,
            border: `1px solid ${estilo.border}`,
            whiteSpace: "nowrap",
          }}
        >
          {estilo.label}
        </span>
      </div>

      {!estaDadoDeAlta && (
        <>
          <div
            style={{
              marginTop: "10px",
              borderRadius: "10px",
              background: "var(--bg)",
              border: "1px solid var(--border-subtle)",
              padding: "8px 8px 4px",
            }}
          >
            <Sparkline valores={historialFc} color={estilo.color} />
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontFamily: "var(--mono)",
                fontSize: "8.5px",
                color: "var(--text-muted)",
                letterSpacing: ".1em",
                padding: "2px 2px 0",
              }}
            >
              <span>FC</span>
              <span>{historialFc.length} lecturas</span>
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "9px",
              margin: "10px 0 0",
            }}
          >
            <VitalMiniStat
              etiqueta="FC"
              valor={ultimaFc ? Number(ultimaFc.valor).toString() : "–"}
              unidad="bpm"
              color={colorFc}
            />
            <VitalMiniStat
              etiqueta="SpO2"
              valor={ultimaSpo2 ? Number(ultimaSpo2.valor).toString() : "–"}
              unidad="%"
              color={colorSpo2}
            />
            <VitalMiniStat
              etiqueta="BP"
              valor={bpTexto}
              unidad="mmHg"
              color={colorBp}
            />
          </div>
        </>
      )}

      <p
        style={{
          margin: "8px 0 0",
          fontSize: "13px",
          color: "var(--text-muted)",
          fontFamily: "var(--mono)",
        }}
      >
        {estaDadoDeAlta
          ? "Sin asignación activa"
          : `Sala ${paciente.sala ?? "s/asignar"} · Cama ${paciente.cama ?? "-"}`}
      </p>
    </Link>
  );
}

export default PatientCard;

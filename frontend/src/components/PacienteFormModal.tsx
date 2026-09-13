import { useState } from "react";
import type { CSSProperties } from "react";
import { usePacienteForm } from "../hooks/usePacienteForm";
import type {
  Paciente,
  PacienteActualizar,
  PacienteCrear,
} from "../types/pacientes";

type ModoFormulario = "crear" | "editar";

interface PacienteFormModalProps {
  abierto: boolean;
  modo: ModoFormulario;
  // Requerido en modo "editar" (para prellenar el form), ignorado en "crear".
  paciente?: Paciente;
  onCerrar: () => void;
  onExito: (resultado: Paciente) => void;
}

type FormState = {
  nombre: string;
  apellido: string;
  documento: string;
  fecha_nacimiento: string;
  genero: string;
  sala: string;
  cama: string;
};

const FORM_VACIO: FormState = {
  nombre: "",
  apellido: "",
  documento: "",
  fecha_nacimiento: "",
  genero: "",
  sala: "",
  cama: "",
};

// Traduce un Paciente (como llega de la API) al shape plano que usan
// los <input> del formulario. Los campos opcionales (genero/sala/cama)
// pueden venir en null desde el backend; el form siempre trabaja con
// "" para que los inputs controlados de React no se quejen.
function pacienteAFormState(paciente: Paciente): FormState {
  return {
    nombre: paciente.nombre,
    apellido: paciente.apellido,
    documento: paciente.documento,
    fecha_nacimiento: paciente.fecha_nacimiento,
    genero: paciente.genero ?? "",
    sala: paciente.sala ?? "",
    cama: paciente.cama ?? "",
  };
}

const ETIQUETA_CAMPO: Record<keyof FormState, string> = {
  nombre: "Nombre",
  apellido: "Apellido",
  documento: "Documento",
  fecha_nacimiento: "Fecha de nacimiento",
  genero: "Género",
  sala: "Sala",
  cama: "Cama",
};

function PacienteFormModal({
  abierto,
  modo,
  paciente,
  onCerrar,
  onExito,
}: PacienteFormModalProps) {
  const [form, setForm] = useState<FormState>(FORM_VACIO);
  // Rastrea si el modal ya estaba abierto en el render anterior. No es
  // un simple booleano de UI: es lo que nos permite distinguir "recién
  // se abrió" (hay que sincronizar el form) de "sigue abierto, el
  // usuario está tipeando" (no hay que tocar el form).
  const [huboAperturaPrevia, setHuboAperturaPrevia] = useState(false);
  const { crearPaciente, actualizarPaciente, enviando, error } =
    usePacienteForm();

  // Patrón recomendado por React para "ajustar estado cuando cambia una
  // prop" (https://react.dev/learn/you-might-not-need-an-effect):
  // llamar a setState directo en el cuerpo del render, NO en un
  // useEffect. Un useEffect acá dispararía un render extra en cascada
  // (efecto corre después del commit, y ese setState agenda otro
  // render) solo para sincronizar algo que ya sabemos en el momento de
  // renderizar. Esta forma actualiza el estado ANTES de pintar, sin
  // ese round-trip.
  //
  // Se ejecuta una sola vez por apertura (abierto pasa de false a
  // true): ahí sincronizamos el form (vacío para "crear", los datos
  // del paciente para "editar"). Al cerrarse, bajamos la bandera para
  // que la PRÓXIMA apertura (mismo paciente u otro) vuelva a
  // sincronizar, y no se quede mostrando datos viejos.
  if (abierto && !huboAperturaPrevia) {
    setHuboAperturaPrevia(true);
    setForm(
      modo === "editar" && paciente ? pacienteAFormState(paciente) : FORM_VACIO,
    );
  } else if (!abierto && huboAperturaPrevia) {
    setHuboAperturaPrevia(false);
  }

  if (!abierto) return null;

  const esEdicion = modo === "editar" && paciente !== undefined;
  const formValido =
    form.nombre.trim() !== "" &&
    form.apellido.trim() !== "" &&
    form.documento.trim() !== "" &&
    form.fecha_nacimiento !== "";

  function actualizarCampo(campo: keyof FormState, valor: string) {
    setForm((previo) => ({ ...previo, [campo]: valor }));
  }

  // Convierte "" -> null para los campos opcionales, así el body que
  // viaja al backend coincide con lo que espera PacienteCrear/
  // PacienteActualizar (string | None), en vez de mandar strings vacíos.
  function aValorOpcional(valor: string): string | null {
    return valor.trim() === "" ? null : valor.trim();
  }

  async function manejarSubmit() {
    if (esEdicion && paciente) {
      // Solo mandamos los campos que realmente cambiaron: así el Evento
      // que registra actualizar_paciente en el backend ("Campos
      // modificados: X -> Y") cuenta la historia real, no un snapshot
      // completo del formulario aunque nada se haya tocado.
      // Comparación campo por campo (en vez de un loop genérico): los
      // obligatorios viajan tal cual si cambiaron, los opcionales pasan
      // por "" -> null. Explícito así TypeScript puede verificar cada
      // asignación contra su tipo real en PacienteActualizar.
      const original = pacienteAFormState(paciente);
      const cambios: PacienteActualizar = {};
      if (form.nombre !== original.nombre) cambios.nombre = form.nombre;
      if (form.apellido !== original.apellido) cambios.apellido = form.apellido;
      if (form.documento !== original.documento)
        cambios.documento = form.documento;
      if (form.fecha_nacimiento !== original.fecha_nacimiento)
        cambios.fecha_nacimiento = form.fecha_nacimiento;
      if (form.genero !== original.genero)
        cambios.genero = aValorOpcional(form.genero);
      if (form.sala !== original.sala) cambios.sala = aValorOpcional(form.sala);
      if (form.cama !== original.cama) cambios.cama = aValorOpcional(form.cama);

      if (Object.keys(cambios).length === 0) {
        // Nada para actualizar: cerramos sin pegarle al backend.
        onCerrar();
        return;
      }

      const resultado = await actualizarPaciente(paciente.id, cambios);
      if (resultado) onExito(resultado);
      return;
    }

    const datos: PacienteCrear = {
      nombre: form.nombre.trim(),
      apellido: form.apellido.trim(),
      documento: form.documento.trim(),
      fecha_nacimiento: form.fecha_nacimiento,
      genero: aValorOpcional(form.genero),
      sala: aValorOpcional(form.sala),
      cama: aValorOpcional(form.cama),
    };
    const resultado = await crearPaciente(datos);
    if (resultado) onExito(resultado);
  }

  const estiloInput: CSSProperties = {
    width: "100%",
    background: "var(--bg-panel-alt)",
    border: "1px solid var(--border-subtle)",
    borderRadius: 8,
    padding: "10px 12px",
    color: "var(--text-h)",
    fontFamily: "var(--sans)",
    fontSize: 14,
    boxSizing: "border-box",
  };

  const estiloLabel: CSSProperties = {
    display: "block",
    fontFamily: "var(--mono)",
    fontSize: 10.5,
    letterSpacing: "0.08em",
    color: "var(--text-muted)",
    marginBottom: 6,
    textTransform: "uppercase",
  };

  function campoTexto(
    campo: keyof FormState,
    opciones: { tipo?: string; requerido?: boolean; placeholder?: string } = {},
  ) {
    return (
      <div style={{ marginBottom: 14 }}>
        <label htmlFor={campo} style={estiloLabel}>
          {ETIQUETA_CAMPO[campo]}
          {opciones.requerido && " *"}
        </label>
        <input
          id={campo}
          type={opciones.tipo ?? "text"}
          placeholder={opciones.placeholder}
          value={form[campo]}
          onChange={(e) => actualizarCampo(campo, e.target.value)}
          style={estiloInput}
        />
      </div>
    );
  }

  return (
    <div
      onClick={onCerrar}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(3, 6, 12, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 460,
          maxWidth: "90vw",
          maxHeight: "88vh",
          overflowY: "auto",
          background: "var(--bg-panel)",
          border: "1px solid var(--border-subtle)",
          borderRadius: 14,
          boxShadow: "0 0 40px rgba(0, 0, 0, 0.35)",
          padding: 22,
          fontFamily: "var(--sans)",
          color: "var(--text-h)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: 18,
          }}
        >
          <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>
            {esEdicion ? "Editar paciente" : "Nuevo paciente"}
          </h2>
          <button
            onClick={onCerrar}
            aria-label="Cerrar"
            style={{
              background: "transparent",
              border: "1px solid var(--border)",
              borderRadius: 6,
              color: "var(--text-h)",
              width: 28,
              height: 28,
              cursor: "pointer",
            }}
          >
            ✕
          </button>
        </div>

        <div
          style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}
        >
          {campoTexto("nombre", { requerido: true })}
          {campoTexto("apellido", { requerido: true })}
        </div>
        {campoTexto("documento", {
          requerido: true,
          placeholder: "Ej. 30111222",
        })}
        {campoTexto("fecha_nacimiento", { tipo: "date", requerido: true })}
        {campoTexto("genero", { placeholder: "Opcional" })}
        <div
          style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}
        >
          {campoTexto("sala", { placeholder: "Opcional" })}
          {campoTexto("cama", { placeholder: "Opcional" })}
        </div>

        {error && (
          <p
            style={{
              color: "var(--color-critica)",
              fontSize: 12.5,
              margin: "-4px 0 12px",
            }}
          >
            {error}
          </p>
        )}

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: 10,
            marginTop: 8,
          }}
        >
          <button
            onClick={onCerrar}
            disabled={enviando}
            style={{
              padding: "10px 18px",
              borderRadius: 8,
              fontFamily: "var(--sans)",
              fontWeight: 600,
              fontSize: 13.5,
              cursor: enviando ? "not-allowed" : "pointer",
              opacity: enviando ? 0.5 : 1,
              background: "transparent",
              border: "1px solid var(--border)",
              color: "var(--text-h)",
            }}
          >
            Cancelar
          </button>
          <button
            onClick={manejarSubmit}
            disabled={enviando || !formValido}
            style={{
              padding: "10px 18px",
              borderRadius: 8,
              fontFamily: "var(--sans)",
              fontWeight: 600,
              fontSize: 13.5,
              cursor: enviando || !formValido ? "not-allowed" : "pointer",
              opacity: enviando || !formValido ? 0.5 : 1,
              background: "var(--color-normal)",
              border: "1px solid var(--color-normal)",
              color: "#06120C",
            }}
          >
            {enviando
              ? "Guardando..."
              : esEdicion
                ? "Guardar cambios"
                : "Crear paciente"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default PacienteFormModal;

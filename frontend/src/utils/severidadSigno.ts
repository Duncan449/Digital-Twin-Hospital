// frontend/src/utils/severidadSigno.ts
import type { NivelSeveridad } from "../types/enums";
import type { TipoSignoVital } from "../types/clinico";

// tipo.rango_* llegan como string desde la API (Decimal de Postgres),
// por eso los convertimos acá con Number(...) antes de comparar.
export function calcularSeveridadSigno(
  valor: number,
  tipo: TipoSignoVital,
): NivelSeveridad {
  const normalMin = Number(tipo.rango_normal_min);
  const normalMax = Number(tipo.rango_normal_max);
  const criticoMin = Number(tipo.rango_critico_min);
  const criticoMax = Number(tipo.rango_critico_max);

  if (valor >= normalMin && valor <= normalMax) {
    return "normal";
  }
  if (valor >= criticoMin && valor < normalMin) {
    return "precaucion";
  }
  if (valor > normalMax && valor <= criticoMax) {
    return "precaucion";
  }
  return "critica";
}

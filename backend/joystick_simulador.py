"""
Simulador FÍSICO de signos vitales usando un joystick

QUÉ HACE:
Lee en loop el estado del joystick y, según qué botón/gatillo/cruceta
esté presionado, va subiendo o bajando el valor de UN signo vital
específico. Cada cierto intervalo, si el valor cambió, lo manda por
HTTP al mismo endpoint que usa el simulador normal:
    POST /pacientes/{id}/signos-vitales

Por qué funciona así:
Este script es un CLIENTE más de tu API, igual que Postman o el
simulador de interpolación lineal que ya tenían. No sabe nada de
Temporal, WebSockets ni el motor de detección. El joystick solo decide 
QUÉ valor mandar y CUÁNDO.

⚠️ IMPORTANTE SOBRE LOS ÍNDICES:
Los números de BOTON_* y EJE_* de acá abajo son los más comunes para
un control de Xbox en Windows con XInput. Si tu gamepad es distinto
(PlayStation, genérico, o estás en Linux/Mac), estos índices pueden
no coincidir. Si al correr el script un botón no hace nada o hace
algo distinto al esperado, corré este mismo archivo con la variable
MODO_DEBUG en True (ver más abajo): vas a ver en consola qué índice
corresponde a cada botón/eje que toques, y ahí ajustás los números.
"""

import json
import time
import uuid

import httpx
import pygame

from app.config.redis_client import CANAL_COORDINACION_SIMULADOR, get_redis_client_sincrono

# CONFIGURACIÓN -- lo que más probablemente necesites ajustar

BASE_URL = "http://localhost:8000"

# Si True, el script solo IMPRIME qué botón/eje tocas
MODO_DEBUG = False

# Índices de botones típicos de un control de Xbox en pygame (Windows/XInput)
BOTON_A = 0
BOTON_B = 1
BOTON_X = 2
BOTON_Y = 3
BOTON_LB = 4
BOTON_RB = 5

# Los gatillos (LT/RT) casi siempre se leen como EJES analógicos, no
# como botones digitales. En XInput suelen ser el eje 2 (LT) y 5 (RT),
# con valores de -1 (soltado) a 1 (apretado a fondo).
EJE_LT = 4
EJE_RT = 5
UMBRAL_EJE = 0.5  # a partir de qué valor consideramos el gatillo "apretado"

# Cuántos pasos hacen falta para recorrer el rango crítico completo del
# signo vital (de mínimo a máximo). Solo se usa para calibrar qué tan
# grande es cada "paso" por tick
PASOS_RECORRIDO = 60

# Piso técnico (no clínico): SignoVitalCrear exige valor > 0 en el
# schema del backend, así que un valor <= 0 sería rechazado con un 422.
# Este mínimo evita mandar un valor inválido, nada más.
VALOR_MINIMO_TECNICO = 0.01

# Saturación de oxígeno es un porcentaje y no puede superar el 100%.
# Es el único signo del catálogo con este tipo de límite.
LIMITE_FISICO_MAX = {
    "saturacion_oxigeno": 100.0,
}

# Cada cuántos segundos, como máximo, se manda una medición al backend
# por signo vital (evita saturar con un POST por cada frame del loop).
INTERVALO_ENVIO_SEG = 0.3

# Frecuencia del loop de lectura del joystick (Hz)
TICK_HZ = 20

# MAPEO: qué controles manejan qué signo vital

# tipo "boton": positivo/negativo son índices de botón digital
# tipo "eje": positivo/negativo son índices de eje analógico (gatillos)
# tipo "hat_y": cruceta arriba (1) / abajo (-1)
# tipo "hat_x": cruceta derecha (1) / izquierda (-1)

CONTROLES = [
    {"signo": "frecuencia_cardiaca", "tipo": "boton", "positivo": BOTON_Y, "negativo": BOTON_A},
    {"signo": "temperatura_corporal", "tipo": "boton", "positivo": BOTON_X, "negativo": BOTON_B},
    {"signo": "saturacion_oxigeno", "tipo": "hat_y", "positivo": 1, "negativo": -1},
    {"signo": "frecuencia_respiratoria", "tipo": "hat_x", "positivo": 1, "negativo": -1},
    {"signo": "presion_sistolica", "tipo": "boton", "positivo": BOTON_RB, "negativo": BOTON_LB},
    {"signo": "presion_diastolica", "tipo": "eje", "positivo": EJE_RT, "negativo": EJE_LT},
]


def obtener_catalogo_signos_vitales(cliente: httpx.Client) -> dict:
    """
    Trae el catálogo real desde la API (GET /tipos-signos-vitales) en
    vez de hardcodear UUIDs a mano. Así, si alguna vez cambian los
    rangos clínicos en Neon, este script no queda desactualizado.
    """
    respuesta = cliente.get(f"{BASE_URL}/tipos-signos-vitales")
    respuesta.raise_for_status()

    catalogo = {}
    for tipo in respuesta.json():
        catalogo[tipo["nombre"]] = {
            "id": tipo["id"],
            "unidad": tipo["unidad"],
            "normal_min": float(tipo["rango_normal_min"]),
            "normal_max": float(tipo["rango_normal_max"]),
            "critico_min": float(tipo["rango_critico_min"]),
            "critico_max": float(tipo["rango_critico_max"]),
        }
    return catalogo


def obtener_ultimos_valores_reales(
    cliente: httpx.Client, paciente_id: uuid.UUID, catalogo: dict
) -> dict[str, float]:
    """
    Trae el historial real del paciente y devuelve, para cada signo que
    ya tenga al menos una medición, su valor más reciente así el
    joystick arranca desde donde el paciente ya estaba.
    """
    respuesta = cliente.get(f"{BASE_URL}/pacientes/{paciente_id}/signos-vitales")
    respuesta.raise_for_status()

    id_a_nombre = {info["id"]: nombre for nombre, info in catalogo.items()}
    ultimos: dict[str, float] = {}
    for medicion in respuesta.json():
        nombre = id_a_nombre.get(medicion["tipo_signo_id"])
        if nombre is not None and nombre not in ultimos:
            ultimos[nombre] = float(medicion["valor"])
    return ultimos


def _publicar_coordinacion(
    tipo: str, paciente_id: uuid.UUID, valores: dict[str, float] | None = None
) -> None:
    """
    Le avisa a monitor_continuo.py que pause o reanude el control
    automático de este paciente, por un canal de Redis aparte del de
    eventos clínicos. Best-effort a propósito: si Redis no está
    levantado, el joystick tiene que poder seguir funcionando igual --
    solo se pierde la coordinación con el otro script, no la simulación.
    """
    try:
        cliente_redis = get_redis_client_sincrono()
        mensaje: dict = {"tipo": tipo, "paciente_id": str(paciente_id)}
        if valores is not None:
            mensaje["valores"] = valores
        cliente_redis.publish(CANAL_COORDINACION_SIMULADOR, json.dumps(mensaje))
    except Exception as error:
        print(f"No se pudo publicar '{tipo}' por Redis: {error}")


def leer_estado_control(joystick: "pygame.joystick.Joystick", control: dict) -> int:
    """
    Devuelve +1 si el control "positivo" está activo, -1 si el
    "negativo" está activo, 0 si ninguno (o ambos a la vez, caso
    borde que ignoramos para no complicar la lógica).
    """
    tipo = control["tipo"]

    if tipo == "boton":
        activo_pos = joystick.get_button(control["positivo"])
        activo_neg = joystick.get_button(control["negativo"])
    elif tipo == "eje":
        activo_pos = joystick.get_axis(control["positivo"]) > UMBRAL_EJE
        activo_neg = joystick.get_axis(control["negativo"]) > UMBRAL_EJE
    elif tipo == "hat_y":
        _, y = joystick.get_hat(0)
        activo_pos = y == control["positivo"]
        activo_neg = y == control["negativo"]
    elif tipo == "hat_x":
        x, _ = joystick.get_hat(0)
        activo_pos = x == control["positivo"]
        activo_neg = x == control["negativo"]
    else:
        return 0

    if activo_pos and not activo_neg:
        return 1
    if activo_neg and not activo_pos:
        return -1
    return 0


def main() -> None:
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No se detectó ningún joystick conectado. Conectalo y volvé a correr el script.")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Joystick detectado: {joystick.get_name()}")

    if MODO_DEBUG:
        print("MODO_DEBUG activo: tocá botones/ejes/cruceta y mirá qué índice se imprime.")
        print("Presioná Ctrl+C para salir.\n")
        reloj = pygame.time.Clock()
        while True:
            pygame.event.pump()
            for i in range(joystick.get_numbuttons()):
                if joystick.get_button(i):
                    print(f"Botón presionado: {i}")
            for i in range(joystick.get_numaxes()):
                valor = joystick.get_axis(i)
                if abs(valor) > 0.5:
                    print(f"Eje {i}: {valor:.2f}")
            if joystick.get_numhats() > 0:
                hat = joystick.get_hat(0)
                if hat != (0, 0):
                    print(f"Cruceta (hat): {hat}")
            reloj.tick(TICK_HZ)

    paciente_id_texto = input("UUID del paciente a simular: ").strip()
    try:
        paciente_id = uuid.UUID(paciente_id_texto)
    except ValueError:
        print("Ese UUID no es válido.")
        return

    cliente = httpx.Client(timeout=5.0)
    catalogo = obtener_catalogo_signos_vitales(cliente)

    # Validamos que los 6 signos del mapeo existan en el catálogo real.
    for control in CONTROLES:
        if control["signo"] not in catalogo:
            print(f"El signo vital '{control['signo']}' no está en el catálogo de la API.")
            return

    # Valor inicial: el punto medio del rango normal de cada signo.
    # Paso por tick: se calibra sobre el tamaño del rango crítico (para
    # que la velocidad de cambio se "sienta" parecida entre signos con
    # escalas distintas), pero el valor en sí puede superarlo sin límite.
    ultimos_valores_reales = obtener_ultimos_valores_reales(cliente, paciente_id, catalogo)

    valor_actual = {}
    paso = {}
    for control in CONTROLES:
        info = catalogo[control["signo"]]
        valor_actual[control["signo"]] = ultimos_valores_reales.get(
            control["signo"], (info["normal_min"] + info["normal_max"]) / 2
        )
        paso[control["signo"]] = (info["critico_max"] - info["critico_min"]) / PASOS_RECORRIDO

    ultimo_valor_enviado = dict(valor_actual)
    ultimo_envio_en = {control["signo"]: 0.0 for control in CONTROLES}

    # A partir de acá el joystick tiene el control de este paciente --
    # monitor_continuo.py, si está corriendo, deja de postear
    # automáticamente para él hasta que se lo avisemos de vuelta.
    _publicar_coordinacion("pausar_paciente", paciente_id)

    print("\nListo. Usá los controles mapeados para mover los signos vitales.")
    print("Ctrl+C para salir.\n")

    reloj = pygame.time.Clock()
    try:
        while True:
            pygame.event.pump()
            ahora = time.time()

            for control in CONTROLES:
                signo = control["signo"]
                info = catalogo[signo]
                direccion = leer_estado_control(joystick, control)

                if direccion != 0:
                    nuevo_valor = valor_actual[signo] + direccion * paso[signo]
                    # Piso técnico (no clínico) para no violar valor > 0.
                    nuevo_valor = max(VALOR_MINIMO_TECNICO, nuevo_valor)
                    # Techo físico, solo para los signos que lo tienen
                    # (hoy, únicamente saturación de oxígeno).
                    limite_max = LIMITE_FISICO_MAX.get(signo)
                    if limite_max is not None:
                        nuevo_valor = min(nuevo_valor, limite_max)
                    valor_actual[signo] = nuevo_valor

                cambio_significativo = abs(valor_actual[signo] - ultimo_valor_enviado[signo]) > 0.05
                paso_intervalo = (ahora - ultimo_envio_en[signo]) >= INTERVALO_ENVIO_SEG

                if cambio_significativo and paso_intervalo:
                    _enviar_medicion(cliente, paciente_id, info["id"], valor_actual[signo], signo, info["unidad"])
                    ultimo_valor_enviado[signo] = valor_actual[signo]
                    ultimo_envio_en[signo] = ahora

            reloj.tick(TICK_HZ)
    except KeyboardInterrupt:
        print("\nSimulación detenida.")
    finally:
        # Le devolvemos el control a monitor_continuo.py con los
        # últimos valores reales que dejamos, para que retome desde ahí
        # en vez de un valor viejo que tenía en memoria de antes de que
        # el joystick tomara el control (evita otro salto, ahora al revés).
        _publicar_coordinacion("reanudar_paciente", paciente_id, valor_actual)
        cliente.close()

def _enviar_medicion(
    cliente: httpx.Client,
    paciente_id: uuid.UUID,
    tipo_signo_id: str,
    valor: float,
    nombre_signo: str,
    unidad: str,
) -> None:
    """POST al mismo endpoint que usa cualquier cliente HTTP. origen='joystick'
    para que quede trazado en la DB de dónde vino esta medición."""
    cuerpo = {
        "tipo_signo_id": tipo_signo_id,
        "valor": round(valor, 2),
        "origen": "joystick",
    }
    try:
        respuesta = cliente.post(
            f"{BASE_URL}/pacientes/{paciente_id}/signos-vitales", json=cuerpo
        )
        respuesta.raise_for_status()
        severidad = respuesta.json().get("severidad_calculada", "?")
        print(f"{nombre_signo}: {valor:.2f} {unidad}  ->  severidad: {severidad}")
    except httpx.HTTPError as error:
        print(f"Error enviando '{nombre_signo}': {error}")


if __name__ == "__main__":
    main()

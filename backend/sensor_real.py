"""
Prototipo conceptual de Gateway de Ingesta

Traduce mensajes MQTT de un sensor físico (ESP32 + MAX30102) al mismo
formato que ya usan los simuladores.
"""

import json

import httpx
import paho.mqtt.client as mqtt

BASE_URL = "http://localhost:8000"
BROKER_MQTT = "localhost"
TOPICO_SENSORES = "hospital/signos-vitales/+"  # el "+" captura cualquier device_id

# Mapeo device_id físico -> (paciente_id, tipo_signo_id). En un
# hospital real esto vendría de una tabla de "device pairing"; acá lo
# resolvemos con un diccionario a mano, a modo de prototipo.
MAPEO_DISPOSITIVOS = {
    "esp32-cama-01": {
        "paciente_id": "PACIENTE_UUID_AQUI",
        "tipo_signo_id": "TIPO_SIGNO_UUID_AQUI",
    },
}

cliente_http = httpx.Client(timeout=5.0)


def _es_valor_fisicamente_plausible(valor: float) -> bool:
    """
    Filtro mínimo antes de mandar el dato: un sensor real puede mandar
    0 (o un valor negativo, por un glitch de lectura) por una
    desconexión momentánea del cable I2C o del WiFi, no porque el
    paciente tenga esa medición. Esto NO reemplaza a
    evaluar_severidad() -- es un filtro técnico, no clínico.
    """
    return valor > 0


def al_recibir_mensaje(client, userdata, mensaje) -> None:
    """
    Callback de paho-mqtt: se dispara automáticamente cada vez que
    llega un mensaje nuevo en TOPICO_SENSORES.
    """
    device_id = mensaje.topic.split("/")[-1]
    dispositivo = MAPEO_DISPOSITIVOS.get(device_id)
    if dispositivo is None:
        print(f"Dispositivo desconocido: {device_id}")
        return

    try:
        payload = json.loads(mensaje.payload)
        valor = float(payload["valor"])
    except (json.JSONDecodeError, KeyError, ValueError) as error:
        print(f"Mensaje inválido de {device_id}: {error}")
        return

    if not _es_valor_fisicamente_plausible(valor):
        print(f"Valor descartado (no plausible) de {device_id}: {valor}")
        return

    _enviar_al_backend(dispositivo, valor)


def _enviar_al_backend(dispositivo: dict, valor: float) -> None:
    cuerpo = {
        "tipo_signo_id": dispositivo["tipo_signo_id"],
        "valor": round(valor, 2),
        "origen": "sensor_real",
    }
    try:
        respuesta = cliente_http.post(
            f"{BASE_URL}/pacientes/{dispositivo['paciente_id']}/signos-vitales",
            json=cuerpo,
        )
        respuesta.raise_for_status()
        severidad = respuesta.json().get("severidad_calculada", "?")
        print(f"Medición enviada: {valor} -> severidad: {severidad}")
    except httpx.HTTPError as error:
        print(f"No se pudo enviar la medición al backend: {error}")


def main() -> None:
    client = mqtt.Client()
    client.on_message = al_recibir_mensaje
    client.connect(BROKER_MQTT)
    client.subscribe(TOPICO_SENSORES)
    print(f"Escuchando sensores en '{TOPICO_SENSORES}'... Ctrl+C para salir.")
    client.loop_forever()


if __name__ == "__main__":
    main()

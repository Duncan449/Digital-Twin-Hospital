from decimal import Decimal


def generar_serie_lineal(
    valor_inicial: Decimal, valor_final: Decimal, cantidad_pasos: int
) -> list[Decimal]:
    """
    Interpolación lineal simple: reparte 'cantidad_pasos' valores
    equidistantes entre valor_inicial y valor_final (ambos incluidos).
    Vive acá (y no en simulador_service.py) porque workflows.py necesita
    importarla directamente, y simulador_service.py ya arrastra un
    import de signos_vitales_service.py que termina llegando de vuelta
    a workflows.py.
    """
    paso = (valor_final - valor_inicial) / (cantidad_pasos - 1)
    return [valor_inicial + paso * i for i in range(cantidad_pasos)]

# HEALTH TWIN — Monitorización hospitalaria basada en Digital Twin

Prototipo académico de un sistema de monitorización sanitaria, presentado en la cátedra de Seminario de Actualización 2 de Ingeniería en Sistemas en la UNLAR. Cada paciente internado tiene un **Digital Twin**: una representación digital que se actualiza en tiempo real a partir de signos vitales simulados y refleja su estado clínico (normal, precaución o crítico).

Los procesos sanitarios, generación de alertas, escalamiento al personal, registro de la intervención y estabilización del paciente, se orquestan con **Temporal**, de modo que siguen su curso aunque algún servicio se caiga o se reinicie.

---
## Equipo de trabajo
Nieto Idiarte Camila Nicole

Herrera Valentino Gabriel

Paez Villegas Tomás Abel

---
## Funcionalidades

- **Dashboard** con todos los pacientes, su severidad actual, KPIs y la lista de alertas activas con cuenta regresiva hasta el escalamiento.
- **Vista Digital Twin** por paciente: gráficos en tiempo real de cada signo vital, línea de tiempo de eventos y panel de simulación.
- **Gestión de pacientes**: alta, edición de datos administrativos y alta médica (*soft delete*: los datos se conservan).
- **Motor de detección**: evalúa cada medición contra los rangos normal/crítico del catálogo y genera alertas, con una ventana de supresión para evitar *alarm fatigue*.
- **Workflows de Temporal**: ciclo de vida completo de cada alerta con timers durables, escalamiento repetido y estabilización gradual tras la intervención.
- **Tiempo real** con WebSockets (el frontend se reconecta solo si se pierde la conexión).
- **Fuentes de datos simulados**: monitor continuo y un joystick de Xbox como "sensor físico".
- **Autenticación** con JWT.

---

## Arquitectura

```mermaid
flowchart LR
    subgraph Simuladores
        MC[monitor_continuo.py]
        JS[joystick_simulador.py]
    end

    subgraph Docker
        TS[Temporal Server :7233]
        TUI[Temporal UI :8080]
        TPG[(Postgres interno de Temporal :5433)]
        RD[(Redis :6379)]
    end

    FE[Frontend React :5173]
    API[FastAPI :8000]
    WK[Worker de Temporal]
    DB[(Neon PostgreSQL)]

    MC -- POST mediciones --> API
    JS -- POST mediciones --> API
    FE -- REST --> API
    API -- WebSocket --> FE
    API --> DB
    API -- inicia workflows / envía signals --> TS
    TS --> TPG
    TUI --> TS
    WK -- ejecuta workflows y activities --> TS
    WK --> DB
    API -- publica eventos --> RD
    WK -- publica eventos --> RD
    RD -- pub/sub --> API
    RD -- pub/sub --> MC
```

El sistema corre como **varios procesos independientes** que se comunican entre sí:

| Proceso | Qué hace |
|---|---|
| **FastAPI** (`uvicorn`) | API REST, motor de detección, gateway de WebSockets. Inicia workflows en Temporal cuando se genera una alerta. |
| **Worker de Temporal** (`temporal/worker.py`) | Ejecuta el código de los workflows y activities. Si se cae, Temporal conserva el estado y el worker retoma al reiniciarse. |
| **Temporal Server** (Docker) | Guarda el historial de cada workflow y cuenta los timers. No ejecuta código de negocio. |
| **Redis** (Docker) | Canal pub/sub que lleva los eventos del worker y de la API al gateway de WebSockets y a los simuladores. No guarda datos clínicos. |
| **Neon** | Base de datos del sistema (pacientes, signos vitales, alertas, intervenciones, eventos). |
| **Monitor continuo** | Genera mediciones periódicas para todos los pacientes activos. |

---

## Stack tecnológico

| Capa | Tecnologías |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Alembic, asyncpg, python-jose, passlib (bcrypt) |
| Orquestación | Temporal (SDK `temporalio` para Python), Temporal Server en Docker |
| Mensajería | Redis 7 (pub/sub), `redis.asyncio` |
| Base de datos | PostgreSQL en Neon |
| Frontend | React 19, TypeScript, Vite, React Router, Recharts |
| Simuladores | httpx, pygame (joystick), paho-mqtt (prototipo de sensor real) |

---

## Estructura del repositorio

```
.
├── requirements.txt             # dependencias de Python
├── backend/
│   ├── docker-compose.yml       # Temporal Server, Temporal UI, su Postgres y Redis
│   ├── alembic.ini
│   ├── .env                     # NO se sube al repo (ver "Configuración")
│   ├── app/
│   │   ├── main.py              # crea la app FastAPI y registra las rutas
│   │   ├── config/              # settings (.env), conexión a la BD y a Redis
│   │   ├── models/              # modelos SQLAlchemy
│   │   ├── schemas/             # modelos Pydantic (entrada/salida de la API)
│   │   ├── services/            # lógica de negocio (incluye deteccion.py)
│   │   ├── routes/              # endpoints REST
│   │   ├── websockets/          # gateway WebSocket + puente con Redis
│   │   ├── core/                # seguridad (hash de contraseñas, JWT)
│   │   ├── dependencies/        # dependencias de FastAPI (usuario autenticado)
│   │   ├── utils/               # helpers compartidos (series de valores)
│   │   └── alembic/             # migraciones de la base de datos
│   ├── temporal/
│   │   ├── worker.py            # proceso que ejecuta workflows y activities
│   │   ├── workflows.py         # AlertaWorkflow (ciclo de vida de una alerta)
│   │   ├── activities.py        # pasos con efectos (BD, Redis)
│   │   └── client.py            # cliente usado por FastAPI para iniciar workflows
│   ├── monitor_continuo.py      # simulador automático de signos vitales
│   ├── joystick_simulador.py    # simulador con joystick de Xbox
│   ├── sensor_real.py           # prototipo conceptual: gateway MQTT para un sensor físico
│   └── seed_admin.py            # crea el usuario administrador inicial
└── frontend/
    └── src/
        ├── pages/               # Login, Dashboard, DigitalTwinView
        ├── components/          # tarjetas, gráficos, modales, panel del simulador
        ├── hooks/               # acceso a la API (usePacientes, useAlertas, ...)
        ├── context/             # AuthContext y EventosWebSocketContext
        ├── services/            # apiFetch, auth y config (URLs del backend)
        ├── constants/ utils/ types/
        └── mocks/               # datos de prueba usados en las primeras fases
```

---

## Requisitos previos

- Python 3.13
- Node.js (versión LTS reciente) y npm
- Docker Desktop
- Una base de datos PostgreSQL en [Neon](https://neon.tech)
- Opcional: un joystick de Xbox para `joystick_simulador.py`

---

## Instalación y configuración

### 1. Backend

Desde la raíz del repositorio:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Variables de entorno

Crear `backend/.env` (no se versiona):

```env
DATABASE_URL=postgresql+asyncpg://usuario:password@host.neon.tech/nombre_bd
SECRET_KEY=clave_generada_con_openssl_rand_hex_32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://localhost:6379
```

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DATABASE_URL` | Sí | Cadena de conexión de Neon con el driver `asyncpg`. |
| `SECRET_KEY` | Sí | Clave para firmar los JWT. Generarla con `openssl rand -hex 32`. |
| `ALGORITHM` | No | Algoritmo de firma. Por defecto `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Duración de la sesión. Por defecto 30. |
| `REDIS_URL` | No | Por defecto `redis://localhost:6379` (el contenedor de Docker). |

### 3. Base de datos

Desde `backend/`:

```bash
alembic upgrade head
```

El **catálogo de signos vitales** (frecuencia cardíaca, frecuencia respiratoria, temperatura corporal, saturación de oxígeno, presión sistólica y diastólica, con sus rangos normal y crítico) y el **rol `admin`** se cargan manualmente en Neon; no se editan desde la API.

Luego, crear el usuario administrador (pide email, nombre y contraseña por consola):

```bash
python seed_admin.py
```

### 4. Frontend

```bash
cd frontend
npm install
```

La URL del backend se configura en `frontend/src/services/config.ts` (por defecto `http://localhost:8000`; la del WebSocket se deriva automáticamente).

---

## Puesta en marcha

Cada proceso va en **su propia terminal**, en este orden (todos los comandos de Python desde `backend/` y con el venv activado):

| # | Proceso | Comando |
|---|---|---|
| 1 | Contenedores (Temporal, Temporal UI, Postgres de Temporal, Redis) | `docker compose up -d` |
| 2 | Worker de Temporal | `python temporal/worker.py` |
| 3 | API FastAPI | `uvicorn app.main:app --reload` |
| 4 | Frontend | `npm run dev` (desde `frontend/`) |
| 5 | Monitor continuo | `python monitor_continuo.py` |
| 6 | Joystick (opcional) | `python joystick_simulador.py` |

El monitor necesita que la API esté levantada, porque al arrancar le pide la lista de pacientes y el catálogo de signos.

Para apagar los contenedores: `docker compose down` (los workflows se conservan en el volumen `temporal-postgres-data`; `docker compose down -v` los borra).

### URLs útiles

| Servicio | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API + documentación interactiva (Swagger) | http://localhost:8000/docs |
| Temporal UI | http://localhost:8080 |

---

## Cómo funciona

### Detección de severidad

Cada medición que llega a `POST /pacientes/{id}/signos-vitales` se evalúa en `services/deteccion.py` contra los rangos del catálogo:

- dentro del rango normal → **normal**
- fuera del normal pero dentro del crítico → **precaución**
- fuera del rango crítico → **crítica**

La severidad del paciente es la peor entre sus signos. Una medición crítica genera una **alerta** e inicia un `AlertaWorkflow` en Temporal, salvo que esté dentro de la ventana de supresión posterior a una alerta resuelta del mismo signo.

### Ciclo de vida de una alerta (`AlertaWorkflow`)

1. **Esperando intervención**: el workflow espera un *signal* de Temporal con la intervención. Si pasa `INTERVALO_ESCALADO` sin respuesta, registra una escalación y vuelve a esperar, tantas veces como haga falta.
2. **Resolviendo**: al registrarse la intervención (`POST /alertas/{id}/intervenciones`), la API envía el signal; el workflow marca la alerta como resuelta (activity con reintentos).
3. **Estabilizando**: el workflow postea una rampa de valores desde el valor crítico hasta el rango normal, con un timer entre cada paso.
4. **Resuelta**: el workflow termina.

Las esperas del workflow son **timers durables**: los cuenta el Temporal Server, no el worker. Por eso, si el worker se detiene en medio de una espera, el workflow continúa exactamente donde estaba cuando el worker vuelve. El estado actual de un workflow se puede consultar con `GET /alertas/{id}/estado-workflow` (query `estado_actual`) o en la Temporal UI.

### Fuentes de datos simulados

- **Monitor continuo** (`monitor_continuo.py`): un loop independiente por cada par (paciente, signo). Cada par alterna entre ruido dentro del rango normal, un deterioro progresivo hasta crítico (espontáneo con cierta probabilidad por tick, o manual desde el botón "deteriorar" de la UI) y una pausa tras la resolución de la alerta.
- **Joystick** (`joystick_simulador.py`): cada botón o gatillo sube o baja un signo vital del paciente elegido, imitando un sensor físico. Mientras se usa, el monitor continuo pausa ese paciente (coordinación por Redis). Si los botones no responden como se espera, poner `MODO_DEBUG = True` para ver los índices del control.
- **Sensor real** (`sensor_real.py`): prototipo conceptual que traduce mensajes MQTT de un dispositivo físico al mismo endpoint que usan los simuladores. No forma parte de la demo.

### Parámetros de tiempo

Los tiempos de la simulación están repartidos entre procesos. Si se modifican, hay que respetar la relación **duración de la rampa < pausa del monitor < ventana de supresión**.

| Constante | Archivo | Qué controla |
|---|---|---|
| `INTERVALO_TICK_SEG` | `backend/monitor_continuo.py` | Cada cuánto postea cada par (paciente, signo). |
| `PROBABILIDAD_DETERIORO_ESPONTANEO` | `backend/monitor_continuo.py` | Probabilidad por tick de iniciar un deterioro. Si cambia el tick, ajustarla en proporción: `P' = P × tick' / tick`. |
| `FRACCION_AVANCE_DETERIORO`, `FRACCION_RUIDO_NORMAL` | `backend/monitor_continuo.py` | Velocidad del deterioro y amplitud del ruido, por tick. |
| `PAUSA_POST_RESOLUCION_SEG` | `backend/monitor_continuo.py` | Tiempo que el monitor no postea tras resolverse una alerta, para no pisar la rampa. |
| `INTERVALO_ESCALADO` | `backend/temporal/workflows.py` | Espera antes de escalar una alerta sin atender. |
| `PASOS_ESTABILIZACION`, `INTERVALO_ESTABILIZACION_SEG` | `backend/temporal/workflows.py` | Rampa de estabilización. Dura `(pasos − 1) × intervalo`. |
| `VENTANA_SUPRESION_SEG` | `backend/app/services/deteccion.py` | Tiempo de gracia en el que no se genera una alerta nueva del mismo signo. |
| `SEGUNDOS_PARA_ESCALAR` | `frontend/src/components/AlertasActivas.tsx` | Cuenta regresiva de la UI; debe coincidir con `INTERVALO_ESCALADO`. |

Al cambiar constantes de `workflows.py`, conviene hacerlo sin alertas abiertas y reiniciar el worker: los workflows en curso ya tienen sus timers registrados con los valores anteriores.

---

## API

La documentación completa e interactiva está en http://localhost:8000/docs. Resumen:

| Recurso | Endpoints |
|---|---|
| Autenticación | `POST /auth/login` |
| Pacientes | `GET/POST /pacientes`, `GET/PATCH /pacientes/{id}`, `PATCH /pacientes/{id}/dar-de-alta` |
| Signos vitales | `GET/POST /pacientes/{id}/signos-vitales`, `POST /pacientes/{id}/signos-vitales/{tipo_signo_id}/deteriorar` |
| Catálogo | `GET /tipos-signos-vitales`, `GET /tipos-signos-vitales/{id}` |
| Alertas | `GET /alertas`, `GET /alertas/{id}`, `GET /alertas/{id}/estado-workflow`, `POST /alertas/estabilizar-todos`, `GET /pacientes/{id}/alertas` |
| Intervenciones | `POST /alertas/{alerta_id}/intervenciones` |
| Eventos | `GET /pacientes/{id}/eventos` |
| Simulador | `POST /pacientes/{id}/simulacion` |
| WebSockets | `ws://localhost:8000/ws/eventos` (global), `ws://localhost:8000/ws/pacientes/{id}` (por paciente) |

---

## Mejoras futuras

- Implementar niveles de autorización y roles de forma más robusta en el proyecto.
- Implementar CRUD de usuarios y roles.
- Dockerizar la API y el worker para que todo arranque con un docker compose up.
- Mejorar las notificaciones al personal, implementando mensajes por correo o SMS desde una activity de Temporal.
- Integrar sensores reales y últimadamente eliminar o separar el apartado de simulaciones.

---

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { WS_URL } from "../services/config";

// Forma de CUALQUIER mensaje que llega por este canal: coincide 1:1 con
// el "mensaje" armado en backend/app/websockets/eventos.py
// (publicar_evento). "tipo" identifica de qué se trata
// (medicion_registrada, alerta_generada, alerta_actualizada,
// alerta_escalada, alerta_resuelta); "data" trae el detalle propio de
// ese tipo puntual.
export interface EventoWS {
  paciente_id: string;
  tipo: string;
  data: Record<string, unknown>;
  timestamp: string;
}

type Escucha = (evento: EventoWS) => void;

interface EventosWebSocketContextValue {
  conectado: boolean;
  suscribir: (escucha: Escucha) => () => void;
}

const EventosWebSocketContext = createContext<EventosWebSocketContextValue | undefined>(undefined);

// Backoff simple: cada intento fallido de reconexión espera más que el
// anterior, hasta un tope de 8s. Evita "machacar" al backend con
// reconexiones instantáneas si Docker/uvicorn están caídos, pero sigue
// intentando solo -- mismo espíritu que la tolerancia a fallos que ya
// tienen con Temporal, aplicado acá al WebSocket.
const DEMORAS_RECONEXION_MS = [1000, 2000, 4000, 8000, 8000];

export function EventosWebSocketProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [conectado, setConectado] = useState(false);

  // Los listeners viven en un ref (Set mutable), NO en un useState:
  // agregarse/sacarse no debe disparar un re-render del Provider ni,
  // mucho menos, una reconexión del socket.
  const escuchasRef = useRef<Set<Escucha>>(new Set());
  const socketRef = useRef<WebSocket | null>(null);
  const intentoRef = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const desmontadoRef = useRef(false);

  const conectar = useCallback(() => {
    const socket = new WebSocket(`${WS_URL}/ws/eventos`);
    socketRef.current = socket;

    socket.onopen = () => {
      intentoRef.current = 0; // reconexión exitosa: se resetea el backoff
      setConectado(true);
    };

    socket.onmessage = (mensaje) => {
      try {
        const evento: EventoWS = JSON.parse(mensaje.data);
        escuchasRef.current.forEach((escucha) => escucha(evento));
      } catch {
        // Un mensaje que no es JSON válido se ignora. No debería pasar
        // nunca (el backend siempre manda json.dumps), pero un parseo
        // roto no tiene por qué tirar abajo la conexión completa.
      }
    };

    socket.onclose = () => {
      setConectado(false);
      socketRef.current = null;
      if (desmontadoRef.current) return; // el Provider se desmontó, no reintentamos

      const demora =
        DEMORAS_RECONEXION_MS[
          Math.min(intentoRef.current, DEMORAS_RECONEXION_MS.length - 1)
        ];
      intentoRef.current += 1;
      timeoutRef.current = setTimeout(conectar, demora);
    };

    // onerror no necesita lógica propia: el navegador siempre dispara
    // 'close' justo después de 'error', así que la reconexión ya queda
    // cubierta en onclose.
    socket.onerror = () => {};
  }, []);

  useEffect(() => {
    desmontadoRef.current = false;
    conectar();

    return () => {
      desmontadoRef.current = true;
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      socketRef.current?.close();
    };
  }, [conectar]);

  const suscribir = useCallback((escucha: Escucha) => {
    escuchasRef.current.add(escucha);
    return () => escuchasRef.current.delete(escucha);
  }, []);

  return (
    <EventosWebSocketContext.Provider value={{ conectado, suscribir }}>
      {children}
    </EventosWebSocketContext.Provider>
  );
}

export function useEventosWebSocket() {
  const ctx = useContext(EventosWebSocketContext);
  if (!ctx) {
    throw new Error(
      "useEventosWebSocket debe usarse dentro de <EventosWebSocketProvider>",
    );
  }
  return ctx;
}
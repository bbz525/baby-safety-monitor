import { create } from 'zustand';

export type VisionEvent = {
  id?: number;
  timestamp: string;
  trackId: string;
  x: number; y: number; w: number; h: number;
  action?: string;
  riskScore?: number;
};

export type Alert = {
  id?: number;
  timestamp: string;
  trackId?: string;
  zoneId?: number;
  level: string;
  reason?: string;
  detailsJson?: string;
};

type State = {
  events: VisionEvent[];
  alerts: Alert[];
  connected: boolean;
  lastError?: string;
  connect: () => void;
};

let currentEs: EventSource | null = null;
let reconnectTimer: number | null = null;

function notifyAlert(title: string, body?: string) {
  if (!('Notification' in window)) return;
  if (Notification.permission === 'granted') {
    new Notification(title, { body });
  } else if (Notification.permission !== 'denied') {
    Notification.requestPermission();
  }
}

export const useStore = create<State>((set, get) => ({
  events: [],
  alerts: [],
  connected: false,
  lastError: undefined,
  connect: () => {
    const base = import.meta.env.VITE_API_BASE || 'http://localhost:8080';
    const url = `${base}/api/events/stream`;

    const start = () => {
      if (currentEs) {
        currentEs.close();
        currentEs = null;
      }
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }

      const es = new EventSource(url);
      currentEs = es;
      es.onopen = () => set({ connected: true, lastError: undefined });
      es.onerror = () => {
        set({ connected: false, lastError: 'SSE disconnected' });
        try { es.close(); } catch {}
        // exponential backoff up to 10s
        let attempts = 0;
        const retry = () => {
          attempts += 1;
          const delay = Math.min(10000, 500 * Math.pow(2, attempts));
          reconnectTimer = window.setTimeout(() => {
            start();
          }, delay) as unknown as number;
        };
        retry();
      };
      es.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          if ('w' in data && 'h' in data && 'x' in data) {
            set({ events: [data, ...get().events].slice(0, 200) });
          } else if ('level' in data) {
            set({ alerts: [data, ...get().alerts].slice(0, 200) });
            notifyAlert(`告警: ${data.level}`, data.reason ?? undefined);
          }
        } catch {
          // ignore
        }
      };
    };

    start();
  },
}));



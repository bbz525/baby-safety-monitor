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
  connect: () => void;
};

export const useStore = create<State>((set, get) => ({
  events: [],
  alerts: [],
  connect: () => {
    const base = import.meta.env.VITE_API_BASE || 'http://localhost:8080';
    const es = new EventSource(`${base}/api/events/stream`);
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if ('w' in data && 'h' in data && 'x' in data) {
          set({ events: [data, ...get().events].slice(0, 200) });
        } else if ('level' in data) {
          set({ alerts: [data, ...get().alerts].slice(0, 200) });
        }
      } catch {
        // ignore
      }
    };
  },
}));



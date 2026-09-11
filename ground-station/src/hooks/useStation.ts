import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ConnStatus, DataService, StationState } from '../services/dataService';
import { RealDataService } from '../services/realDataService';
import { MockDataService } from '../mock/mockDataService';
import { isRealMode } from '../firebase/config';
import { uid } from '../utils/format';

export interface Toast {
  id: string;
  kind: 'sos' | 'info' | 'warn' | 'ok';
  text: string;
}

const EMPTY: StationState = { helmets: {}, locations: {}, cameras: {}, messages: {}, alerts: [], events: [] };

export function useStation() {
  const [state, setState] = useState<StationState>(EMPTY);
  const [conn, setConn] = useState<ConnStatus>('connecting');
  const [toasts, setToasts] = useState<Toast[]>([]);
  // suppress toast spam from the initial RTDB backlog on startup
  const quietUntil = useRef(Date.now() + 3000);

  const service = useMemo<DataService>(
    () => (isRealMode ? new RealDataService() : new MockDataService()),
    [],
  );

  const pushToast = useCallback((kind: Toast['kind'], text: string, ttl = 5000) => {
    const id = uid();
    setToasts((prev) => [...prev.slice(-4), { id, kind, text }]);
    window.setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), ttl);
  }, []);

  useEffect(() => {
    quietUntil.current = Date.now() + 3000;
    service.start({
      onState: setState,
      onConn: setConn,
      onEvent: (e) => {
        if (Date.now() < quietUntil.current) return;
        switch (e.type) {
          case 'helmet_online': pushToast('ok', `${e.helmetId} is ONLINE`); break;
          case 'helmet_offline': pushToast('warn', `${e.helmetId} went OFFLINE`); break;
          case 'camera_online': pushToast('ok', `${e.helmetId} camera online`); break;
          case 'camera_offline': pushToast('warn', `${e.helmetId} camera offline`); break;
          default: break;
        }
      },
      onAlert: (a) => {
        if (Date.now() < quietUntil.current) return;
        pushToast('sos', `SOS! ${a.helmetId} · ${a.type} · ${new Date(a.timestamp).toLocaleTimeString()}`, 12000);
      },
      onMessage: (m) => {
        if (Date.now() < quietUntil.current) return;
        if (m.direction === 'helmet_to_gs') pushToast('info', `Message from ${m.helmetId}: ${m.text.slice(0, 40)}`);
      },
    });
    return () => service.dispose();
  }, [service, pushToast]);

  return { state, conn, toasts, service, mode: service.mode };
}

import type { Database } from 'firebase/database';
import { limitToLast, onChildAdded, onValue, push, query, ref, set, update } from 'firebase/database';
import { getDb } from '../firebase/config';
import type { ConnStatus, DataHandlers, DataService, StationState } from './dataService';
import type { Alert, Camera, Helmet, LocationPoint, Message, TimelineEvent } from '../models/types';
import { HELMET_IDS } from '../models/constants';
import { uid } from '../utils/format';

/** Live Firebase RTDB implementation of DataService (REAL mode). */
export class RealDataService implements DataService {
  readonly mode = 'REAL' as const;
  private db: Database;
  private handlers: DataHandlers | null = null;
  private unsubs: Array<() => void> = [];
  private state: StationState = { helmets: {}, locations: {}, cameras: {}, messages: {}, alerts: [], events: [] };

  constructor() {
    const db = getDb();
    if (!db) throw new Error('RealDataService requires Firebase env configuration');
    this.db = db;
  }

  start(handlers: DataHandlers): void {
    this.handlers = handlers;

    this.unsubs.push(
      onValue(ref(this.db, '.info/connected'), (snap) => {
        handlers.onConn((snap.val() === true ? 'connected' : 'offline') as ConnStatus);
      }),
    );

    this.unsubs.push(
      onValue(ref(this.db, 'helmets'), (snap) => {
        const raw = (snap.val() ?? {}) as Record<string, Record<string, unknown>>;
        const helmets: Record<string, Helmet> = {};
        for (const [id, v] of Object.entries(raw)) {
          helmets[id] = {
            id,
            name: (v.name as string) ?? id,
            status: v.status === 'online' ? 'online' : 'offline',
            lastSeen: typeof v.lastSeen === 'number' ? v.lastSeen : null,
            battery: typeof v.battery === 'number' ? v.battery : null,
          };
        }
        this.state.helmets = helmets;
        this.emit();
      }),
    );

    this.unsubs.push(
      onValue(ref(this.db, 'locations'), (snap) => {
        const raw = (snap.val() ?? {}) as Record<string, Record<string, unknown>>;
        const locations: Record<string, LocationPoint> = {};
        for (const [id, v] of Object.entries(raw)) {
          if (typeof v.lat === 'number' && typeof v.lng === 'number') {
            locations[id] = {
              helmetId: id,
              lat: v.lat,
              lng: v.lng,
              timestamp: typeof v.timestamp === 'number' && v.timestamp > 0 ? v.timestamp : Date.now(),
            };
          }
        }
        this.state.locations = locations;
        this.emit();
      }),
    );

    this.unsubs.push(
      onValue(ref(this.db, 'cameras'), (snap) => {
        const raw = (snap.val() ?? {}) as Record<string, Record<string, unknown>>;
        const cameras: Record<string, Camera> = {};
        for (const [id, v] of Object.entries(raw)) {
          const status: Camera['status'] =
            v.status === 'online' ? 'online' : v.status === 'mock' ? 'mock' : v.status === 'unconfigured' ? 'unconfigured' : 'offline';
          cameras[id] = {
            id: (v.id as string) ?? `CAM_${id.slice(-2)}`,
            helmetId: id,
            streamUrl: (v.streamUrl as string) ?? null,
            status,
          };
        }
        this.state.cameras = cameras;
        this.emit();
      }),
    );

    this.unsubs.push(
      onValue(ref(this.db, 'alerts'), (snap) => {
        const raw = (snap.val() ?? {}) as Record<string, Record<string, unknown>>;
        this.state.alerts = Object.entries(raw)
          .map(([id, v]) => this.normAlert(id, v))
          .sort((a, b) => b.timestamp - a.timestamp);
        this.emit();
      }),
    );

    this.unsubs.push(
      onChildAdded(ref(this.db, 'alerts'), (snap) => {
        const id = snap.key;
        if (!id) return;
        const a = this.normAlert(id, (snap.val() ?? {}) as Record<string, unknown>);
        if (!a.acknowledged) this.handlers?.onAlert(a);
      }),
    );

    const eventsQ = query(ref(this.db, 'events'), limitToLast(200));
    this.unsubs.push(
      onChildAdded(eventsQ, (snap) => {
        const e = this.normEvent(snap.key ?? uid(), (snap.val() ?? {}) as Record<string, unknown>);
        this.state.events = [e, ...this.state.events.filter((x) => x.id !== e.id)].slice(0, 200);
        this.state.events.sort((a, b) => b.timestamp - a.timestamp);
        this.handlers?.onEvent(e);
        this.emit();
      }),
    );

    for (const id of HELMET_IDS) {
      this.state.messages[id] = [];
      const mq = query(ref(this.db, `messages/${id}`), limitToLast(100));
      this.unsubs.push(
        onChildAdded(mq, (snap) => {
          const m = this.normMessage(id, snap.key ?? uid(), (snap.val() ?? {}) as Record<string, unknown>);
          const list = this.state.messages[id] ?? [];
          this.state.messages[id] = [...list.filter((x) => x.id !== m.id), m].slice(-100);
          this.handlers?.onMessage(m);
          this.emit();
        }),
      );
    }
  }

  sendMessage(helmetId: string, text: string): void {
    const payload = { helmetId, direction: 'gs_to_helmet', text, timestamp: Date.now(), status: 'sent' };
    void push(ref(this.db, `messages/${helmetId}`), payload);
  }

  acknowledgeAlert(alertId: string): void {
    void update(ref(this.db, `alerts/${alertId}`), { acknowledged: true, status: 'acknowledged' });
  }

  /**
   * Push a real GPS fix (e.g. from PhoneLocationProvider) into Firebase.
   * Also marks the helmet online — a device that just reported GPS is
   * genuinely reporting, so this is real status, not a fake heartbeat.
   */
  pushExternalLocation(helmetId: string, lat: number, lng: number): void {
    const now = Date.now();
    void set(ref(this.db, `locations/${helmetId}`), { helmetId, lat, lng, timestamp: now });
    void update(ref(this.db, `helmets/${helmetId}`), {
      id: helmetId,
      name: `Helmet ${helmetId.slice(-2)}`,
      status: 'online',
      lastSeen: now,
    });
  }

  // mock-only controls
  triggerSos(): void { console.info('[REAL] triggerSos is a mock-only control'); }
  toggleHelmetOnline(): void { console.info('[REAL] toggleHelmetOnline is a mock-only control'); }
  toggleCamera(): void { console.info('[REAL] toggleCamera is a mock-only control'); }
  simulateLocation(): void { console.info('[REAL] simulateLocation is a mock-only control'); }

  dispose(): void {
    this.unsubs.forEach((u) => u());
    this.unsubs = [];
    this.handlers = null;
  }

  private emit(): void {
    this.handlers?.onState({
      helmets: { ...this.state.helmets },
      locations: { ...this.state.locations },
      cameras: { ...this.state.cameras },
      messages: { ...this.state.messages },
      alerts: [...this.state.alerts],
      events: [...this.state.events],
    });
  }

  private normAlert(id: string, v: Record<string, unknown>): Alert {
    return {
      id,
      helmetId: (v.helmetId as string) ?? 'UNKNOWN',
      type: (v.type as Alert['type']) ?? 'SOS',
      timestamp: typeof v.timestamp === 'number' && v.timestamp > 0 ? v.timestamp : Date.now(),
      status: v.acknowledged === true ? 'acknowledged' : 'active',
      acknowledged: v.acknowledged === true,
    };
  }

  private normEvent(id: string, v: Record<string, unknown>): TimelineEvent {
    return {
      id,
      helmetId: (v.helmetId as string) ?? 'UNKNOWN',
      type: (v.type as TimelineEvent['type']) ?? 'location_update',
      message: (v.message as string) ?? '',
      timestamp: typeof v.timestamp === 'number' && v.timestamp > 0 ? v.timestamp : Date.now(),
    };
  }

  private normMessage(helmetId: string, id: string, v: Record<string, unknown>): Message {
    return {
      id,
      helmetId,
      direction: v.direction === 'helmet_to_gs' ? 'helmet_to_gs' : 'gs_to_helmet',
      text: (v.text as string) ?? '',
      timestamp: typeof v.timestamp === 'number' && v.timestamp > 0 ? v.timestamp : Date.now(),
      status: (v.status as Message['status']) ?? 'sent',
    };
  }
}
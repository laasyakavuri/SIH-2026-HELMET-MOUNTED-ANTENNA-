import type { DataHandlers, DataService, StationState } from '../services/dataService';
import type { Alert, Camera, Helmet, LocationPoint, Message, TimelineEvent } from '../models/types';
import { HELMET_IDS } from '../models/constants';
import { truncate, uid } from '../utils/format';

interface WalkState { lat: number; lng: number; heading: number; }

const START: Record<string, WalkState> = {
  HELMET_01: { lat: 28.6125, lng: 77.2050, heading: 40 },
  HELMET_02: { lat: 28.6252, lng: 77.2190, heading: 140 },
  HELMET_03: { lat: 28.6052, lng: 77.1985, heading: 230 },
  HELMET_04: { lat: 28.6185, lng: 77.2305, heading: 320 },
};

const TICK_MS = 2000;
const MAX_EVENTS = 200;
const MAX_ALERTS = 100;
const MAX_MSGS = 100;

/** Full in-browser simulation. Everything it produces is MOCK. */
export class MockDataService implements DataService {
  readonly mode = 'MOCK' as const;
  private handlers: DataHandlers | null = null;
  private timer: ReturnType<typeof setInterval> | null = null;
  private tick = 0;
  private state: StationState;

  constructor() {
    const now = Date.now();
    const helmets: Record<string, Helmet> = {};
    const locations: Record<string, LocationPoint> = {};
    const cameras: Record<string, Camera> = {};
    const messages: Record<string, Message[]> = {};
    HELMET_IDS.forEach((id, i) => {
      const n = id.slice(-2);
      helmets[id] = { id, name: `Helmet ${n}`, status: 'online', lastSeen: now, battery: 92 - i * 6 };
      locations[id] = { helmetId: id, lat: START[id].lat, lng: START[id].lng, timestamp: now };
      cameras[id] = { id: `CAM_${n}`, helmetId: id, streamUrl: null, status: 'mock' };
      messages[id] = [];
    });
    this.state = { helmets, locations, cameras, messages, alerts: [], events: [] };
  }

  start(handlers: DataHandlers): void {
    this.handlers = handlers;
    handlers.onConn('connected'); // mock layer is always "connected"
    handlers.onState(this.snapshot());
    this.timer = setInterval(() => this.onTick(), TICK_MS);
  }

  dispose(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    this.handlers = null;
  }

  sendMessage(helmetId: string, text: string): void {
    const m: Message = { id: uid(), helmetId, direction: 'gs_to_helmet', text, timestamp: Date.now(), status: 'sent' };
    this.pushMsg(helmetId, m);
    this.addEvent('message_sent', helmetId, `GS -> ${helmetId}: "${truncate(text, 36)}"`);
    this.emit();
    window.setTimeout(() => { m.status = 'delivered'; this.emit(); }, 1200);
    window.setTimeout(() => {
      const reply: Message = {
        id: uid(),
        helmetId,
        direction: 'helmet_to_gs',
        text: `[MOCK] ${this.hname(helmetId)} received: "${truncate(text, 18)}"`,
        timestamp: Date.now(),
        status: 'delivered',
      };
      this.pushMsg(helmetId, reply);
      this.addEvent('message_received', helmetId, `${helmetId} acknowledged GS message`);
      this.handlers?.onMessage(reply);
      this.emit();
    }, 2600);
  }

  acknowledgeAlert(alertId: string): void {
    const a = this.state.alerts.find((x) => x.id === alertId);
    if (!a || a.acknowledged) return;
    a.acknowledged = true;
    a.status = 'acknowledged';
    this.addEvent('alert_acknowledged', a.helmetId, `${a.type} alert acknowledged by operator`);
    this.emit();
  }

  triggerSos(helmetId: string): void {
    const a: Alert = { id: uid(), helmetId, type: 'SOS', timestamp: Date.now(), status: 'active', acknowledged: false };
    this.state.alerts = [a, ...this.state.alerts].slice(0, MAX_ALERTS);
    this.addEvent('sos_triggered', helmetId, `${helmetId} SOS triggered (mock button)`);
    this.handlers?.onAlert(a);
    this.emit();
  }

  toggleHelmetOnline(helmetId: string): void {
    const h = this.state.helmets[helmetId];
    if (!h) return;
    if (h.status === 'online') {
      h.status = 'offline';
      h.lastSeen = Date.now();
      this.addEvent('helmet_offline', helmetId, `${helmetId} went offline`);
    } else {
      h.status = 'online';
      h.lastSeen = Date.now();
      this.addEvent('helmet_online', helmetId, `${helmetId} came online`);
    }
    this.emit();
  }

  toggleCamera(helmetId: string): void {
    const c = this.state.cameras[helmetId];
    if (!c) return;
    if (c.status === 'mock') {
      c.status = 'offline';
      this.addEvent('camera_offline', helmetId, `${c.id} mock feed went offline`);
    } else {
      c.status = 'mock';
      this.addEvent('camera_online', helmetId, `${c.id} mock feed online`);
    }
    this.emit();
  }

  simulateLocation(helmetId: string): void {
    const loc = this.state.locations[helmetId];
    if (!loc) return;
    loc.lat += (Math.random() - 0.5) * 0.02;
    loc.lng += (Math.random() - 0.5) * 0.02;
    loc.timestamp = Date.now();
    this.addEvent('location_update', helmetId, `Simulated GPS jump -> ${loc.lat.toFixed(5)}, ${loc.lng.toFixed(5)}`);
    this.emit();
  }

  pushExternalLocation(helmetId: string, lat: number, lng: number): void {
    const loc = this.state.locations[helmetId];
    if (!loc) return;
    loc.lat = lat;
    loc.lng = lng;
    loc.timestamp = Date.now();
    const h = this.state.helmets[helmetId];
    if (h) h.lastSeen = loc.timestamp;
    this.addEvent('location_update', helmetId, `External GPS push -> ${lat.toFixed(5)}, ${lng.toFixed(5)}`);
    this.emit();
  }

  // -- internals --

  private hname(id: string): string { return `Helmet ${id.slice(-2)}`; }

  private pushMsg(helmetId: string, m: Message): void {
    const list = this.state.messages[helmetId] ?? [];
    this.state.messages[helmetId] = [...list, m].slice(-MAX_MSGS);
  }

  private addEvent(type: TimelineEvent['type'], helmetId: string, message: string): void {
    const e: TimelineEvent = { id: uid(), helmetId, type, message, timestamp: Date.now() };
    this.state.events = [e, ...this.state.events].slice(0, MAX_EVENTS);
    this.handlers?.onEvent(e);
  }

  private snapshot(): StationState {
    return JSON.parse(JSON.stringify(this.state)) as StationState;
  }

  private emit(): void {
    this.handlers?.onState(this.snapshot());
  }

  private onTick(): void {
    this.tick++;
    const now = Date.now();
    HELMET_IDS.forEach((id) => {
      const h = this.state.helmets[id];
      if (h.status !== 'online') return;
      const w = START[id];
      w.heading += Math.random() * 50 - 25;
      const step = 0.00028; // ~30 m per tick
      w.lat += Math.cos((w.heading * Math.PI) / 180) * step;
      w.lng += Math.sin((w.heading * Math.PI) / 180) * step;
      const loc = this.state.locations[id];
      loc.lat = w.lat;
      loc.lng = w.lng;
      loc.timestamp = now;
      h.lastSeen = now;
      if (h.battery != null) h.battery = Math.max(5, h.battery - 0.02);
      if (this.tick % 10 === Math.floor(Math.random() * 10)) {
        this.addEvent('location_update', id, `GPS -> ${loc.lat.toFixed(5)}, ${loc.lng.toFixed(5)}`);
      }
    });
    this.emit();
  }
}

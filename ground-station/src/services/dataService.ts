import type { Alert, Message, TimelineEvent, Helmet, LocationPoint, Camera } from '../models/types';

export type ConnStatus = 'connecting' | 'connected' | 'offline';

export interface StationState {
  helmets: Record<string, Helmet>;
  locations: Record<string, LocationPoint>;
  cameras: Record<string, Camera>;
  messages: Record<string, Message[]>;
  alerts: Alert[];
  events: TimelineEvent[];
}

export interface DataHandlers {
  onState: (s: StationState) => void;
  onConn: (c: ConnStatus) => void;
  onEvent: (e: TimelineEvent) => void;
  onAlert: (a: Alert) => void;
  onMessage: (m: Message) => void;
}

export interface DataService {
  readonly mode: 'REAL' | 'MOCK';
  start(handlers: DataHandlers): void;
  dispose(): void;

  // two-way actions (work in both modes)
  sendMessage(helmetId: string, text: string): void;
  acknowledgeAlert(alertId: string): void;

  // demo/mock controls (no-ops in REAL mode)
  triggerSos(helmetId: string): void;
  toggleHelmetOnline(helmetId: string): void;
  toggleCamera(helmetId: string): void;
  simulateLocation(helmetId: string): void;

  // external location push (PhoneLocationProvider -> Firebase/mock)
  pushExternalLocation(helmetId: string, lat: number, lng: number): void;
}

export type HelmetStatus = 'online' | 'offline';

export interface Helmet {
  id: string;
  name: string;
  status: HelmetStatus;
  lastSeen: number | null;
  battery: number | null;
}

export interface LocationPoint {
  helmetId: string;
  lat: number;
  lng: number;
  timestamp: number;
}

export type MessageDirection = 'gs_to_helmet' | 'helmet_to_gs';
export type MessageStatus = 'sent' | 'delivered' | 'read' | 'failed';

export interface Message {
  id: string;
  helmetId: string;
  direction: MessageDirection;
  text: string;
  timestamp: number;
  status: MessageStatus;
}

export type AlertType = 'SOS' | 'IMPACT' | 'MAN_DOWN' | 'GEOFENCE';

export interface Alert {
  id: string;
  helmetId: string;
  type: AlertType;
  timestamp: number;
  status: 'active' | 'acknowledged';
  acknowledged: boolean;
}

export type CameraStatus = 'online' | 'offline' | 'mock' | 'unconfigured';

export interface Camera {
  id: string;
  helmetId: string;
  streamUrl: string | null;
  status: CameraStatus;
}

export type EventType =
  | 'helmet_online'
  | 'helmet_offline'
  | 'location_update'
  | 'sos_triggered'
  | 'alert_acknowledged'
  | 'message_sent'
  | 'message_received'
  | 'camera_online'
  | 'camera_offline';

export interface TimelineEvent {
  id: string;
  helmetId: string;
  type: EventType;
  message: string;
  timestamp: number;
}

import type { TimelineEvent } from '../models/types';
import { fmtAgo } from '../utils/format';

const LABEL: Record<string, string> = {
  helmet_online: 'ONLINE',
  helmet_offline: 'OFFLINE',
  location_update: 'GPS',
  sos_triggered: 'SOS',
  alert_acknowledged: 'ACK',
  message_sent: 'MSG →',
  message_received: 'MSG ←',
  camera_online: 'CAM ON',
  camera_offline: 'CAM OFF',
};

export default function TimelinePanel({ events, helmetId }: { events: TimelineEvent[]; helmetId: string }) {
  const list = events.filter((e) => e.helmetId === helmetId).slice(0, 40);
  return (
    <section className="panel">
      <div className="panel-h">
        <span>Activity Timeline</span>
        <span className="pill dim">{helmetId}</span>
      </div>
      <div className="timeline">
        {list.length === 0 && <div className="empty">No activity for this helmet yet.</div>}
        {list.map((e) => (
          <div key={e.id} className={`tl-item t-${e.type}`}>
            <span className="tl-dot" />
            <div className="tl-body">
              <div className="tl-head">
                <span className="tl-type">{LABEL[e.type] ?? e.type}</span>
                <span className="tl-time">{fmtAgo(e.timestamp)}</span>
              </div>
              <div className="tl-msg">{e.message}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

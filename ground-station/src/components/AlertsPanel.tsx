import type { Alert } from '../models/types';
import { fmtTime } from '../utils/format';

interface Props {
  alerts: Alert[];
  selectedId: string;
  onSelect: (id: string) => void;
  onAck: (id: string) => void;
}

export default function AlertsPanel({ alerts, selectedId, onSelect, onAck }: Props) {
  const sorted = [...alerts].sort((a, b) => {
    if (a.acknowledged !== b.acknowledged) return a.acknowledged ? 1 : -1;
    return b.timestamp - a.timestamp;
  });
  const activeCount = sorted.filter((a) => !a.acknowledged).length;

  return (
    <section className="panel">
      <div className="panel-h">
        <span>SOS / Alerts</span>
        <span className={`pill ${activeCount > 0 ? 'bad' : 'dim'}`}>{activeCount} ACTIVE</span>
      </div>
      <div className="alert-list">
        {sorted.length === 0 && <div className="empty">No alerts. System nominal.</div>}
        {sorted.map((a) => (
          <div key={a.id} className={`alert ${a.acknowledged ? 'acked' : 'active'} ${a.helmetId === selectedId ? 'for-selected' : ''}`}>
            <div className="alert-top">
              <span className={`badge ${a.acknowledged ? 'dim' : 'bad'}`}>{a.type}</span>
              <button className="link" onClick={() => onSelect(a.helmetId)}>{a.helmetId}</button>
              <span className="alert-time">{fmtTime(a.timestamp)}</span>
            </div>
            <div className="alert-bottom">
              <span className="alert-status">{a.acknowledged ? 'ACKNOWLEDGED' : 'UNACKNOWLEDGED'}</span>
              {!a.acknowledged && (
                <button className="btn small danger" onClick={() => onAck(a.id)}>ACKNOWLEDGE</button>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

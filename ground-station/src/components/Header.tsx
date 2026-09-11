import { useEffect, useState } from 'react';
import type { ConnStatus } from '../services/dataService';

interface Props {
  mode: 'REAL' | 'MOCK';
  conn: ConnStatus;
  onlineCount: number;
  total: number;
}

export default function Header({ mode, conn, onlineCount, total }: Props) {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const i = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(i);
  }, []);

  const fbLabel =
    mode === 'MOCK' ? 'FIREBASE: MOCK'
      : conn === 'connected' ? 'FIREBASE: LIVE'
      : conn === 'connecting' ? 'FIREBASE: CONNECTING'
      : 'FIREBASE: OFFLINE';
  const fbClass = mode === 'MOCK' ? 'badge mock' : conn === 'connected' ? 'badge ok' : conn === 'connecting' ? 'badge warn' : 'badge bad';

  return (
    <header className="header">
      <div className="brand">
        <div className="brand-mark" />
        <div>
          <div className="brand-title">SIH SMART HELMET</div>
          <div className="brand-sub">GROUND CONTROL STATION</div>
        </div>
      </div>
      <div className="header-badges">
        <span className={`badge ${mode === 'REAL' ? 'ok' : 'mock'}`}>MODE: {mode}</span>
        <span className={fbClass}>{fbLabel}</span>
        <span className={`badge ${onlineCount > 0 ? 'ok' : 'bad'}`}>{onlineCount}/{total} HELMETS ONLINE</span>
        <span className="badge dim">{now.toLocaleTimeString([], { hour12: false })}</span>
      </div>
    </header>
  );
}

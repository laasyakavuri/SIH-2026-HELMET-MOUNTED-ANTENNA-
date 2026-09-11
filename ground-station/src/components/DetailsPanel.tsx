import type { ReactNode } from 'react';
import type { StationState } from '../services/dataService';
import { helmetName } from '../models/constants';
import { cameraState } from '../utils/camera';
import { fmtAgo, fmtTime, truncate } from '../utils/format';

interface RowProps { k: string; v: ReactNode; cls?: string; }

function Row({ k, v, cls }: RowProps) {
  return (
    <div className="row">
      <span className="rk">{k}</span>
      <span className={`rv ${cls ?? ''}`}>{v}</span>
    </div>
  );
}

export default function DetailsPanel({ state, helmetId }: { state: StationState; helmetId: string }) {
  const h = state.helmets[helmetId];
  const loc = state.locations[helmetId];
  const cam = cameraState(state.cameras[helmetId], helmetId);
  const msgs = state.messages[helmetId] ?? [];
  const lastMsg = msgs[msgs.length - 1];
  const lastEvt = state.events.find((e) => e.helmetId === helmetId);
  const sosActive = state.alerts.some((a) => a.helmetId === helmetId && !a.acknowledged);

  return (
    <section className="panel">
      <div className="panel-h">
        <span>Helmet Details · {helmetName(helmetId)}</span>
        <span className={`badge ${h?.status === 'online' ? 'ok' : 'bad'}`}>
          {h ? h.status.toUpperCase() : 'UNKNOWN'}
        </span>
      </div>
      <div className="details">
        <Row k="HELMET ID" v={helmetId} />
        <Row k="ONLINE" v={h ? (h.status === 'online' ? 'YES' : 'NO') : '—'} cls={h?.status === 'online' ? 'ok-text' : 'bad-text'} />
        <Row k="LATITUDE" v={loc ? loc.lat.toFixed(6) : '—'} />
        <Row k="LONGITUDE" v={loc ? loc.lng.toFixed(6) : '—'} />
        <Row k="LAST LOCATION UPDATE" v={loc ? `${fmtTime(loc.timestamp)} (${fmtAgo(loc.timestamp)})` : '—'} />
        <Row k="BATTERY" v={h?.battery != null ? `${Math.round(h.battery)}%` : 'not reported'} />
        <Row k="CAMERA" v={cam.mode} cls={cam.mode === 'REAL' ? 'ok-text' : cam.mode === 'MOCK' ? 'warn-text' : 'bad-text'} />
        <Row k="SOS STATE" v={sosActive ? 'SOS ACTIVE' : 'CLEAR'} cls={sosActive ? 'bad-text blink' : 'ok-text'} />
        <Row k="LAST EVENT" v={lastEvt ? `${lastEvt.type} · ${fmtAgo(lastEvt.timestamp)}` : '—'} />
        <Row k="LAST MESSAGE" v={lastMsg ? truncate(lastMsg.text, 30) : '—'} />
      </div>
    </section>
  );
}

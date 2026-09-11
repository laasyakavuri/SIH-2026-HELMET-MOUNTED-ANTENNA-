import type { StationState } from '../services/dataService';
import { HELMET_IDS, helmetName } from '../models/constants';
import { fmtAgo } from '../utils/format';

interface Props { state: StationState; selectedId: string; onSelect: (id: string) => void; }

export default function HelmetList({ state, selectedId, onSelect }: Props) {
  return (
    <section className="panel">
      <div className="panel-h">
        <span>Helmet Fleet</span>
        <span className="pill dim">{HELMET_IDS.length} UNITS</span>
      </div>
      <div className="helmet-list">
        {HELMET_IDS.map((id) => {
          const h = state.helmets[id];
          const online = h?.status === 'online';
          return (
            <button
              key={id}
              className={`helmet-item ${id === selectedId ? 'selected' : ''}`}
              onClick={() => onSelect(id)}
            >
              <span className={`dot ${online ? 'ok' : 'bad'}`} />
              <span className="hi-name">{helmetName(id)}</span>
              <span className="hi-meta">
                {online ? 'ONLINE' : 'OFFLINE'} · {fmtAgo(h?.lastSeen ?? null)}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

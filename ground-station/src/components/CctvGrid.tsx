import { useEffect, useState } from 'react';
import type { StationState } from '../services/dataService';
import { HELMET_IDS, helmetName } from '../models/constants';
import { cameraState } from '../utils/camera';

interface Props { state: StationState; selectedId: string; onSelect: (id: string) => void; }

function MockFeed() {
  const [t, setT] = useState(() => new Date());
  useEffect(() => {
    const i = setInterval(() => setT(new Date()), 1000);
    return () => clearInterval(i);
  }, []);
  return (
    <div className="mock-feed">
      <div className="mock-noise" />
      <div className="mock-scan" />
      <div className="mock-osd">
        <span>MOCK FEED · SIMULATED</span>
        <span>{t.toLocaleTimeString([], { hour12: false })}</span>
      </div>
    </div>
  );
}

export default function CctvGrid({ state, selectedId, onSelect }: Props) {
  const [enlarged, setEnlarged] = useState<string | null>(null);

  return (
    <section className="panel">
      <div className="panel-h">
        <span>CCTV Surveillance</span>
        <span className="pill dim">CLICK FEED TO ENLARGE</span>
      </div>
      <div className={`cctv-grid ${enlarged ? 'has-enlarged' : ''}`}>
        {HELMET_IDS.map((id) => {
          const cs = cameraState(state.cameras[id], id);
          const sel = id === selectedId;
          const big = enlarged === id;
          return (
            <div key={id} className={`cctv ${sel ? 'selected' : ''} ${big ? 'enlarged' : ''}`} onClick={() => onSelect(id)}>
              <div className="cctv-h">
                <span>CAM {id.slice(-2)} · {helmetName(id)}</span>
                <span className={`badge ${cs.mode === 'REAL' ? 'ok' : cs.mode === 'MOCK' ? 'mock' : 'bad'}`}>{cs.mode}</span>
              </div>
              <div
                className="cctv-body"
                onClick={(e) => {
                  e.stopPropagation();
                  setEnlarged(big ? null : id);
                }}
              >
                {cs.mode === 'REAL' && cs.url ? (
                  <img className="cctv-stream" src={cs.url} alt={`${helmetName(id)} live stream`} />
                ) : cs.mode === 'MOCK' ? (
                  <MockFeed />
                ) : (
                  <div className="cctv-offline">NO SIGNAL</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

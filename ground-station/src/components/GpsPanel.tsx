import { useEffect, useRef, useState } from 'react';
import type { DataService } from '../services/dataService';
import { helmetName } from '../models/constants';
import { PhoneLocationProvider } from '../location/phoneLocationProvider';
import { MockLocationProvider } from '../location/mockLocationProvider';

interface FixInfo {
  lat: number;
  lng: number;
  acc?: number;
  source: 'PHONE_GPS' | 'MOCK_GPS';
}

interface Props {
  helmetId: string;
  service: DataService;
  mode: 'REAL' | 'MOCK';
}

const MIN_PUSH_MS = 5000; // throttle Firebase pushes while tracking

export default function GpsPanel({ helmetId, service, mode }: Props) {
  const [fix, setFix] = useState<FixInfo | null>(null);
  const [status, setStatus] = useState('idle');
  const [tracking, setTracking] = useState(false);
  const watchId = useRef<number | null>(null);
  const lastPush = useRef(0);
  const helmetRef = useRef(helmetId);
  helmetRef.current = helmetId;

  const push = (lat: number, lng: number, acc?: number, source: FixInfo['source'] = 'PHONE_GPS') => {
    setFix({ lat, lng, acc, source });
    service.pushExternalLocation(helmetRef.current, lat, lng);
    setStatus('pushed to ' + helmetRef.current);
  };

  const pushOnce = async () => {
    const phone = new PhoneLocationProvider();
    if (phone.isAvailable()) {
      try {
        const f = await phone.getCurrentFix();
        push(f.lat, f.lng, f.accuracy, 'PHONE_GPS');
        return;
      } catch {
        // fall through
      }
    }
    if (mode === 'REAL') {
      setStatus('GPS unavailable/denied - nothing pushed (REAL mode never fakes data)');
      return;
    }
    const m = await new MockLocationProvider().getCurrentFix();
    push(m.lat, m.lng, undefined, 'MOCK_GPS');
  };

  const startTracking = () => {
    if (!('geolocation' in navigator)) {
      setStatus('Geolocation not available in this browser');
      return;
    }
    setStatus('tracking…');
    watchId.current = navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude: lat, longitude: lng, accuracy: acc } = pos.coords;
        const now = Date.now();
        setFix({ lat, lng, acc, source: 'PHONE_GPS' });
        if (now - lastPush.current >= MIN_PUSH_MS) {
          lastPush.current = now;
          service.pushExternalLocation(helmetRef.current, lat, lng);
          setStatus('live · pushing every 5 s');
        }
      },
      (err) => setStatus('GPS error: ' + err.message),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 5000 },
    );
    setTracking(true);
  };

  const stopTracking = () => {
    if (watchId.current != null) {
      navigator.geolocation.clearWatch(watchId.current);
      watchId.current = null;
    }
    setTracking(false);
    setStatus('stopped');
  };

  // stop watch when panel unmounts
  useEffect(
    () => () => {
      if (watchId.current != null) navigator.geolocation.clearWatch(watchId.current);
    },
    [],
  );

  return (
    <section className="panel">
      <div className="panel-h">
        <span>Phone GPS · {helmetName(helmetId)}</span>
        <span className={`badge ${tracking ? 'ok' : 'dim'}`}>
          {tracking ? 'TRACKING LIVE' : mode === 'REAL' ? 'REAL GPS' : 'DEMO GPS'}
        </span>
      </div>
      <div style={{ padding: '4px 0 10px' }}>
        <div className="row">
          <span className="rk">LAST FIX</span>
          <span className="rv">{fix ? `${fix.lat.toFixed(6)}, ${fix.lng.toFixed(6)}` : '—'}</span>
        </div>
        <div className="row">
          <span className="rk">SOURCE</span>
          <span className={`rv ${fix?.source === 'MOCK_GPS' ? 'warn-text' : 'ok-text'}`}>{fix?.source ?? '—'}</span>
        </div>
        <div className="row">
          <span className="rk">ACCURACY</span>
          <span className="rv">{fix?.acc != null ? `±${Math.round(fix.acc)} m` : '—'}</span>
        </div>
        <div className="row">
          <span className="rk">STATUS</span>
          <span className="rv">{status}</span>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', padding: '10px 12px 4px' }}>
          {!tracking && <button className="btn" onClick={pushOnce}>PUSH GPS ONCE</button>}
          {!tracking
            ? <button className="btn danger" onClick={startTracking}>START LIVE TRACKING</button>
            : <button className="btn" onClick={stopTracking}>STOP TRACKING</button>}
        </div>
        <div style={{ padding: '6px 12px', fontSize: 11, color: '#7c8b9d' }}>
          Sends this device's real GPS → Firebase → live map (phone-GPS architecture).
          Tracking follows the currently selected helmet.
        </div>
      </div>
    </section>
  );
}
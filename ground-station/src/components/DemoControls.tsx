import { useState } from 'react';
import type { DataService } from '../services/dataService';
import { helmetName } from '../models/constants';
import { MockLocationProvider } from '../location/mockLocationProvider';
import { PhoneLocationProvider } from '../location/phoneLocationProvider';

interface Props { helmetId: string; service: DataService; }

export default function DemoControls({ helmetId, service }: Props) {
  const [gpsMsg, setGpsMsg] = useState<string | null>(null);

  const pushDeviceGps = async () => {
    const phone = new PhoneLocationProvider();
    try {
      const fix = phone.isAvailable() ? await phone.getCurrentFix() : await new MockLocationProvider().getCurrentFix();
      service.pushExternalLocation(helmetId, fix.lat, fix.lng);
      setGpsMsg(`${fix.source === 'phone' ? 'PHONE_GPS' : 'MOCK_GPS'}: ${fix.lat.toFixed(5)}, ${fix.lng.toFixed(5)}`);
    } catch {
      const fix = await new MockLocationProvider().getCurrentFix();
      service.pushExternalLocation(helmetId, fix.lat, fix.lng);
      setGpsMsg(`MOCK_GPS fallback: ${fix.lat.toFixed(5)}, ${fix.lng.toFixed(5)}`);
    }
    setTimeout(() => setGpsMsg(null), 4000);
  };

  return (
    <div className="demo-bar">
      <span className="demo-label">DEMO CONTROLS (MOCK) · TARGET: {helmetName(helmetId).toUpperCase()}</span>
      <button className="btn danger" onClick={() => service.triggerSos(helmetId)}>TRIGGER SOS</button>
      <button className="btn" onClick={() => service.toggleHelmetOnline(helmetId)}>TOGGLE ONLINE</button>
      <button className="btn" onClick={() => service.toggleCamera(helmetId)}>TOGGLE CAMERA</button>
      <button className="btn" onClick={() => service.simulateLocation(helmetId)}>SIMULATE LOCATION</button>
      <button className="btn" onClick={pushDeviceGps}>PUSH THIS DEVICE GPS</button>
      {gpsMsg && <span className="demo-gps">{gpsMsg}</span>}
    </div>
  );
}

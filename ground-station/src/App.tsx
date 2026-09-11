import { useState } from 'react';
import { useStation } from './hooks/useStation';
import { HELMET_IDS } from './models/constants';
import Header from './components/Header';
import HelmetList from './components/HelmetList';
import AlertsPanel from './components/AlertsPanel';
import MapPanel from './components/MapPanel';
import CctvGrid from './components/CctvGrid';
import DetailsPanel from './components/DetailsPanel';
import GpsPanel from './components/GpsPanel';
import MessagingPanel from './components/MessagingPanel';
import TimelinePanel from './components/TimelinePanel';
import DemoControls from './components/DemoControls';
import Toasts from './components/Toasts';

export default function App() {
  const { state, conn, toasts, service, mode } = useStation();
  const [selectedId, setSelectedId] = useState<string>(HELMET_IDS[0]);
  const onlineCount = HELMET_IDS.filter((id) => state.helmets[id]?.status === 'online').length;

  return (
    <div className="app">
      <Header mode={mode} conn={conn} onlineCount={onlineCount} total={HELMET_IDS.length} />

      {mode === 'MOCK' && (
        <div className="mock-banner">
          DEMO MODE — all helmets, GPS movement, cameras and alerts on this screen are
          <strong> MOCK (simulated)</strong>. Add Firebase credentials in .env for REAL mode.
        </div>
      )}

      <main className="layout">
        <div className="col col-left">
          <HelmetList state={state} selectedId={selectedId} onSelect={setSelectedId} />
          <AlertsPanel
            alerts={state.alerts}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onAck={(id) => service.acknowledgeAlert(id)}
          />
        </div>

        <div className="col col-center">
          <MapPanel state={state} selectedId={selectedId} onSelect={setSelectedId} />
          <CctvGrid state={state} selectedId={selectedId} onSelect={setSelectedId} />
        </div>

        <div className="col col-right">
          <DetailsPanel state={state} helmetId={selectedId} />
          <GpsPanel helmetId={selectedId} service={service} mode={mode} />
          <MessagingPanel
            helmetId={selectedId}
            messages={state.messages[selectedId] ?? []}
            onSend={(t) => service.sendMessage(selectedId, t)}
          />
          <TimelinePanel events={state.events} helmetId={selectedId} />
        </div>
      </main>

      {mode === 'MOCK' && <DemoControls helmetId={selectedId} service={service} />}
      <Toasts toasts={toasts} />
    </div>
  );
}
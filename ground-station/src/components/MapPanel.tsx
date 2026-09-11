import { useEffect } from 'react';
import L from 'leaflet';
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { StationState } from '../services/dataService';
import { HELMET_IDS, helmetName, MAP_CENTER } from '../models/constants';
import { fmtAgo } from '../utils/format';

interface Props { state: StationState; selectedId: string; onSelect: (id: string) => void; }

function MapFocus({ lat, lng, keyId }: { lat: number; lng: number; keyId: string }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([lat, lng], Math.max(map.getZoom(), 14), { duration: 0.8 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keyId]);
  return null;
}

export default function MapPanel({ state, selectedId, onSelect }: Props) {
  const selectedLoc = state.locations[selectedId];
  return (
    <section className="panel map-panel">
      <div className="panel-h">
        <span>Live Map</span>
        <span className="pill dim">{selectedLoc ? 'GPS DATA · OSM TILES' : 'NO FIX'}</span>
      </div>
      <div className="map-wrap">
        <MapContainer center={MAP_CENTER} zoom={13} scrollWheelZoom>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {HELMET_IDS.map((id) => {
            const loc = state.locations[id];
            const h = state.helmets[id];
            if (!loc || !h) return null;
            const online = h.status === 'online';
            const sel = id === selectedId;
            const icon = L.divIcon({
              className: 'hm-wrap',
              html: `<div class="hm ${online ? 'online' : 'offline'} ${sel ? 'selected' : ''}"><span>${id.slice(-2)}</span></div>`,
              iconSize: [36, 36],
              iconAnchor: [18, 18],
            });
            return (
              <Marker key={id} position={[loc.lat, loc.lng]} icon={icon} eventHandlers={{ click: () => onSelect(id) }}>
                <Popup>
                  <div className="popup">
                    <strong>{helmetName(id)}</strong>
                    <div>STATUS: {online ? 'ONLINE' : 'OFFLINE'}</div>
                    <div>LAT: {loc.lat.toFixed(6)}</div>
                    <div>LNG: {loc.lng.toFixed(6)}</div>
                    <div>UPDATED: {fmtAgo(loc.timestamp)}</div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
          {selectedLoc && <MapFocus lat={selectedLoc.lat} lng={selectedLoc.lng} keyId={selectedId} />}
        </MapContainer>
      </div>
    </section>
  );
}

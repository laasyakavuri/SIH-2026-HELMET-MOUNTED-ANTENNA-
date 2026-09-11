/**
 * Location abstraction: phone GPS feeds Firebase, Firebase feeds the map.
 * No GPS hardware (no NEO-6M) anywhere in this system.
 */
export interface LocationFix {
  lat: number;
  lng: number;
  accuracy?: number;
  timestamp: number;
  source: 'mock' | 'phone';
}

export interface LocationProvider {
  readonly name: 'MOCK_GPS' | 'PHONE_GPS';
  isAvailable(): boolean;
  getCurrentFix(): Promise<LocationFix>;
}

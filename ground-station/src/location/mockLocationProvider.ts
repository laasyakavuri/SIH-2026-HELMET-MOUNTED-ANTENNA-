import type { LocationFix, LocationProvider } from './locationProvider';

export class MockLocationProvider implements LocationProvider {
  readonly name = 'MOCK_GPS' as const;
  private t = 0;

  isAvailable(): boolean { return true; }

  getCurrentFix(): Promise<LocationFix> {
    this.t += 0.012;
    const fix: LocationFix = {
      lat: 28.6139 + Math.sin(this.t) * 0.012,
      lng: 77.2090 + Math.cos(this.t) * 0.012,
      timestamp: Date.now(),
      source: 'mock',
    };
    return Promise.resolve(fix);
  }
}

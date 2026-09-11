import type { LocationFix, LocationProvider } from './locationProvider';

/**
 * REAL phone GPS via the browser Geolocation API (works on the device
 * running the Ground Station, e.g. a phone/tablet). Feeds Firebase.
 */
export class PhoneLocationProvider implements LocationProvider {
  readonly name = 'PHONE_GPS' as const;

  isAvailable(): boolean {
    return typeof navigator !== 'undefined' && 'geolocation' in navigator;
  }

  getCurrentFix(): Promise<LocationFix> {
    return new Promise((resolve, reject) => {
      if (!this.isAvailable()) {
        reject(new Error('Geolocation API unavailable'));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) =>
          resolve({
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
            timestamp: pos.timestamp,
            source: 'phone',
          }),
        (err) => reject(err),
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 },
      );
    });
  }
}

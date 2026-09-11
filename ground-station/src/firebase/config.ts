import { initializeApp, type FirebaseApp } from 'firebase/app';
import { getDatabase, type Database } from 'firebase/database';

const env = import.meta.env;

export const firebaseConfig = {
  apiKey: env.VITE_FIREBASE_API_KEY ?? '',
  authDomain: env.VITE_FIREBASE_AUTH_DOMAIN ?? '',
  databaseURL: env.VITE_FIREBASE_DATABASE_URL ?? '',
  projectId: env.VITE_FIREBASE_PROJECT_ID ?? '',
  storageBucket: env.VITE_FIREBASE_STORAGE_BUCKET ?? '',
  messagingSenderId: env.VITE_FIREBASE_MESSAGING_SENDER_ID ?? '',
  appId: env.VITE_FIREBASE_APP_ID ?? '',
};

const forceDemo = (env.VITE_DEMO_MODE ?? '').toLowerCase() === 'true';

export const firebaseConfigured = Boolean(
  firebaseConfig.apiKey && firebaseConfig.databaseURL && firebaseConfig.projectId,
);

/** REAL mode only when credentials exist AND demo not forced. */
export const isRealMode = firebaseConfigured && !forceDemo;

let app: FirebaseApp | null = null;
let db: Database | null = null;

export function getDb(): Database | null {
  if (!isRealMode) return null;
  if (!app) {
    app = initializeApp(firebaseConfig);
    db = getDatabase(app);
  }
  return db;
}

/** Env-configured ESP32-CAM stream URLs (empty string = not configured). */
export const cameraStreamUrls: Record<string, string> = {
  HELMET_01: env.VITE_CAMERA_HELMET_01_URL ?? '',
  HELMET_02: env.VITE_CAMERA_HELMET_02_URL ?? '',
  HELMET_03: env.VITE_CAMERA_HELMET_03_URL ?? '',
  HELMET_04: env.VITE_CAMERA_HELMET_04_URL ?? '',
};

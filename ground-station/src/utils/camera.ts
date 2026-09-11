import { cameraStreamUrls } from '../firebase/config';
import type { Camera } from '../models/types';

export interface CamState {
  mode: 'REAL' | 'MOCK' | 'OFFLINE';
  url: string | null;
}

/**
 * Resolves what a CCTV tile should show. Never claims REAL unless a real
 * stream URL exists (env var or RTDB) and the camera isn't marked offline.
 */
export function cameraState(cam: Camera | undefined, helmetId: string): CamState {
  const envUrl = cameraStreamUrls[helmetId] || cam?.streamUrl || '';
  const status = cam?.status ?? 'offline';
  if (envUrl && status !== 'offline') return { mode: 'REAL', url: envUrl };
  if (status === 'mock') return { mode: 'MOCK', url: null };
  return { mode: 'OFFLINE', url: null };
}

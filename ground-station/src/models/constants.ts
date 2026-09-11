export const HELMET_IDS = ['HELMET_01', 'HELMET_02', 'HELMET_03', 'HELMET_04'] as const;

export const helmetName = (id: string): string => `Helmet ${id.slice(-2)}`;

export const MAP_CENTER: [number, number] = [28.6139, 77.2090];

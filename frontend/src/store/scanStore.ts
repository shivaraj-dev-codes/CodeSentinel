/**
 * Zustand scan store — real-time scan progress state.
 */
import { create } from "zustand";

export interface ScanProgress {
  scanId: string;
  percent: number;
  status: string;
  message: string;
  isConnected: boolean;
}

interface ScanState {
  progress: Record<string, ScanProgress>;
  setProgress: (scanId: string, update: Partial<ScanProgress>) => void;
  clearProgress: (scanId: string) => void;
}

export const useScanStore = create<ScanState>((set) => ({
  progress: {},

  setProgress: (scanId, update) =>
    set((s) => ({
      progress: {
        ...s.progress,
        [scanId]: {
          scanId,
          percent: 0,
          status: "pending",
          message: "",
          isConnected: false,
          ...s.progress[scanId],
          ...update,
        },
      },
    })),

  clearProgress: (scanId) =>
    set((s) => {
      const next = { ...s.progress };
      delete next[scanId];
      return { progress: next };
    }),
}));

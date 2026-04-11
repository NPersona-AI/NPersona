import { create } from "zustand";
import { persist } from "zustand/middleware";
import { useEffect, useState } from "react";

/** Returns true once the Zustand persist store has rehydrated from localStorage. */
export function useHasHydrated() {
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => {
    // If already hydrated by the time this effect runs, set immediately
    if (useAppStore.persist.hasHydrated()) {
      setHydrated(true);
      return;
    }
    const unsub = useAppStore.persist.onFinishHydration(() => setHydrated(true));
    return unsub;
  }, []);
  return hydrated;
}

interface PersonaData {
  id: string;
  name: string;
  team: string; // "user_centric" or "adversarial"
  role?: string;
  alias?: string;
  skill_level?: string;
  attack_taxonomy_ids?: string[];
  risk_severity?: string;
  composite_score?: number;
  source_node_id?: string;
  // Details
  description?: string;
  conversation_trajectory?: any[];
  playbook?: any[];
}

interface AppState {
  currentStep: number;
  jobId: string | null;
  jobStatus: string | null;
  logs: Array<{ id: string; timestamp: Date; message: string; type: string; }>;
  graphData: { nodes: any[]; edges: any[] } | null;
  personas: PersonaData[];
  numUserPersonas: number;
  numAdversarialPersonas: number;

  // Actions
  setStep: (step: number) => void;
  setJobId: (id: string | null) => void;
  setJobStatus: (status: string | null) => void;
  addLog: (message: string, type?: string) => void;
  clearLogs: () => void;
  setGraphData: (data: { nodes: any[]; edges: any[] } | null) => void;
  setPersonas: (personas: PersonaData[]) => void;
  addPersona: (persona: PersonaData) => void;
  setNumUserPersonas: (n: number) => void;
  setNumAdversarialPersonas: (n: number) => void;
  resetJob: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      currentStep: 1,
      jobId: null,
      jobStatus: null,
      logs: [],
      graphData: null,
      personas: [],
      numUserPersonas: 15,
      numAdversarialPersonas: 15,

      setStep: (step) => set({ currentStep: step }),
      setJobId: (id) => set({ jobId: id }),
      setJobStatus: (status) => set({ jobStatus: status }),
      addLog: (message, type = "info") =>
        set((state) => ({
          logs: [
            ...state.logs,
            { id: Math.random().toString(36).substr(2, 9), timestamp: new Date(), message, type },
          ],
        })),
      clearLogs: () => set({ logs: [] }),
      setGraphData: (data) => set({ graphData: data }),
      setPersonas: (personas) => set({ personas }),
      addPersona: (persona) => set((state) => ({ personas: [...state.personas, persona] })),
      setNumUserPersonas: (n) => set({ numUserPersonas: n }),
      setNumAdversarialPersonas: (n) => set({ numAdversarialPersonas: n }),
      resetJob: () => set({ jobId: null, jobStatus: null, currentStep: 1, logs: [], graphData: null, personas: [] }),
    }),
    {
      name: "npersona-store",
      version: 2, // bumped to clear stale localStorage (old max was 30, now 100)
      partialize: (state) => ({
        jobId: state.jobId,
        currentStep: state.currentStep,
        numUserPersonas: state.numUserPersonas,
        numAdversarialPersonas: state.numAdversarialPersonas,
      }),
    }
  )
);

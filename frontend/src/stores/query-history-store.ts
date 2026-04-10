import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { QueryMode } from "@/types/query";

export interface QueryHistoryEntry {
  id: string;
  question: string;
  mode: QueryMode;
  answer: string;
  modeUsed: string | null;
  timestamp: number;
}

interface QueryHistoryState {
  entries: QueryHistoryEntry[];
  add: (entry: Omit<QueryHistoryEntry, "id" | "timestamp">) => void;
  clear: () => void;
}

export const useQueryHistoryStore = create<QueryHistoryState>()(
  persist(
    (set) => ({
      entries: [],
      add: (entry) =>
        set((s) => ({
          entries: [
            { ...entry, id: crypto.randomUUID(), timestamp: Date.now() },
            ...s.entries,
          ].slice(0, 50),
        })),
      clear: () => set({ entries: [] }),
    }),
    { name: "cmms-query-history" },
  ),
);

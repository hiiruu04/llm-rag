import { create } from "zustand";
import { persist } from "zustand/middleware";

interface ChatStore {
  activeSessionId: string | null;
  setActiveSession: (id: string | null) => void;
  clearActiveSession: () => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set) => ({
      activeSessionId: null,
      setActiveSession: (id: string | null) => set({ activeSessionId: id }),
      clearActiveSession: () => set({ activeSessionId: null }),
    }),
    { name: "cmms-active-chat" },
  ),
);
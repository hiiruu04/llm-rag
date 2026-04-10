import type { ReactNode } from "react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { useSidebarStore } from "@/stores/sidebar-store";

export function AppLayout({ children }: { children: ReactNode }) {
  const collapsed = useSidebarStore((s) => s.collapsed);
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className={`flex-1 overflow-y-auto p-6 ${collapsed ? "" : ""}`}>
          {children}
        </main>
      </div>
    </div>
  );
}

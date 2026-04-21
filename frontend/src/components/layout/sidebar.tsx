import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Server,
  AlertTriangle,
  Wrench,
  FileText,
  MessageSquare,
  Network,
  Heart,
  ChevronLeft,
  ChevronRight,
  Users,
  Shield,
  Award,
  Layers,
  ListChecks,
  Bug,
  Package,
  Clock,
  AlertOctagon,
  ClipboardList,
  MapPin,
  Cpu,
  BoxSelect,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSidebarStore } from "@/stores/sidebar-store";

const navSections = [
  {
    label: "Overview",
    items: [
      { to: "/", icon: LayoutDashboard, label: "Dashboard" },
      { to: "/assets", icon: Server, label: "Assets" },
    ],
  },
  {
    label: "Operations",
    items: [
      { to: "/faults", icon: AlertTriangle, label: "Faults" },
      { to: "/maintenance", icon: Wrench, label: "Maintenance" },
      { to: "/orders", icon: ClipboardList, label: "Orders" },
      { to: "/down-events", icon: AlertOctagon, label: "Down Events" },
      { to: "/documents", icon: FileText, label: "Documents" },
    ],
  },
  {
    label: "Resources",
    items: [
      { to: "/workers", icon: Users, label: "Workers" },
      { to: "/roles", icon: Shield, label: "Roles" },
      { to: "/competences", icon: Award, label: "Competences" },
      { to: "/levels", icon: Layers, label: "Levels" },
      { to: "/shifts", icon: Clock, label: "Shifts" },
    ],
  },
  {
    label: "Task Management",
    items: [
      { to: "/tasks", icon: ListChecks, label: "Tasks" },
      { to: "/causes", icon: Bug, label: "Causes" },
      { to: "/materials", icon: Package, label: "Materials" },
    ],
  },
  {
    label: "Infrastructure",
    items: [
      { to: "/locations", icon: MapPin, label: "Locations" },
      { to: "/systems", icon: Cpu, label: "Systems" },
      { to: "/aggregates", icon: BoxSelect, label: "Aggregates" },
    ],
  },
  {
    label: "AI",
    items: [
      { to: "/query", icon: MessageSquare, label: "Query" },
    ],
  },
  {
    label: "Admin",
    items: [
      { to: "/admin/graph", icon: Network, label: "Graph" },
      { to: "/health", icon: Heart, label: "Health" },
    ],
  },
];

export function Sidebar() {
  const { collapsed, toggle } = useSidebarStore();
  const location = useLocation();

  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r border-sidebar-border bg-sidebar-background transition-all duration-200",
        collapsed ? "w-16" : "w-56",
      )}
    >
      <div className="flex h-14 items-center border-b border-sidebar-border px-4">
        {!collapsed && (
          <span className="text-lg font-semibold text-sidebar-foreground">CMMS</span>
        )}
        <button
          onClick={toggle}
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-md text-sidebar-foreground hover:bg-sidebar-accent",
            collapsed ? "mx-auto" : "ml-auto",
          )}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
      <nav className="flex-1 overflow-y-auto p-2">
        {navSections.map((section) => (
          <div key={section.label} className="mb-4">
            {!collapsed && (
              <div className="mb-1 px-2 text-xs font-medium uppercase tracking-wider text-sidebar-foreground/50">
                {section.label}
              </div>
            )}
            {section.items.map((item) => {
              const active = location.pathname === item.to || (item.to !== "/" && location.pathname.startsWith(item.to));
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-2 py-2 text-sm transition-colors",
                    active
                      ? "bg-sidebar-primary text-sidebar-primary-foreground"
                      : "text-sidebar-foreground hover:bg-sidebar-accent",
                    collapsed && "justify-center",
                  )}
                  title={collapsed ? item.label : undefined}
                >
                  <item.icon className="h-4 w-4 shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
    </aside>
  );
}

import { useLocation, Link } from "react-router-dom";
import { Moon, Sun } from "lucide-react";
import { useThemeStore } from "@/stores/theme-store";

const routeLabels: Record<string, string> = {
  "/": "Dashboard",
  "/assets": "Assets",
  "/faults": "Faults",
  "/maintenance": "Maintenance",
  "/documents": "Documents",
  "/query": "AI Query",
  "/admin/graph": "Graph Admin",
  "/health": "Health",
};

function getBreadcrumbs(pathname: string) {
  const parts = pathname.split("/").filter(Boolean);
  const crumbs: { label: string; to: string }[] = [];
  let path = "";
  for (const part of parts) {
    path += `/${part}`;
    const label = routeLabels[path] || part;
    crumbs.push({ label, to: path });
  }
  return crumbs;
}

export function Header() {
  const { isDark, toggle } = useThemeStore();
  const location = useLocation();
  const crumbs = getBreadcrumbs(location.pathname);

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-6">
      <nav className="flex items-center gap-1 text-sm">
        {crumbs.map((crumb, i) => (
          <span key={crumb.to} className="flex items-center gap-1">
            {i > 0 && <span className="text-muted-foreground">/</span>}
            {i < crumbs.length - 1 ? (
              <Link to={crumb.to} className="text-muted-foreground hover:text-foreground">
                {crumb.label}
              </Link>
            ) : (
              <span className="font-medium">{crumb.label}</span>
            )}
          </span>
        ))}
      </nav>
      <button
        onClick={toggle}
        className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground"
        aria-label="Toggle theme"
      >
        {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </button>
    </header>
  );
}

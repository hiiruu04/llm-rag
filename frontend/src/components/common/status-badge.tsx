import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "success" | "warning" | "destructive" | "info";

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-muted text-muted-foreground",
  success: "bg-green-500/15 text-green-600 dark:text-green-400",
  warning: "bg-yellow-500/15 text-yellow-600 dark:text-yellow-400",
  destructive: "bg-red-500/15 text-red-600 dark:text-red-400",
  info: "bg-blue-500/15 text-blue-600 dark:text-blue-400",
};

interface StatusBadgeProps {
  value: string;
  variant?: BadgeVariant;
  map?: Record<string, BadgeVariant>;
}

const defaultMap: Record<string, BadgeVariant> = {
  active: "success",
  inactive: "default",
  maintenance: "warning",
  decommissioned: "destructive",
  faulty: "destructive",
  open: "info",
  investigating: "warning",
  resolved: "success",
  closed: "default",
  low: "default",
  medium: "warning",
  high: "destructive",
  critical: "destructive",
  scheduled: "info",
  in_progress: "warning",
  completed: "success",
  cancelled: "default",
  overdue: "destructive",
  preventive: "info",
  corrective: "warning",
  predictive: "success",
};

export function StatusBadge({ value, map = defaultMap }: StatusBadgeProps) {
  const variant = map[value] ?? "default";
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", variantStyles[variant])}>
      {value.replace(/_/g, " ")}
    </span>
  );
}

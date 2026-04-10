import { InboxIcon } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ title = "No data", description = "There's nothing here yet.", action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <InboxIcon className="h-10 w-10 text-muted-foreground" />
      <h3 className="mt-4 text-sm font-medium">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

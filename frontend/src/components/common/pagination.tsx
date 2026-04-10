import { ChevronLeft, ChevronRight } from "lucide-react";
import type { Pagination } from "@/types/api";

interface PaginationControlsProps {
  pagination: Pagination | null;
  onPageChange: (page: number) => void;
}

export function PaginationControls({ pagination, onPageChange }: PaginationControlsProps) {
  if (!pagination) return null;
  const { page, total_pages } = pagination;
  if (total_pages <= 1) return null;

  return (
    <div className="flex items-center justify-between px-2 py-4">
      <p className="text-sm text-muted-foreground">
        Page {page} of {total_pages} ({pagination.total} total)
      </p>
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="flex h-8 w-8 items-center justify-center rounded-md border border-border text-sm disabled:opacity-50 hover:bg-accent"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= total_pages}
          className="flex h-8 w-8 items-center justify-center rounded-md border border-border text-sm disabled:opacity-50 hover:bg-accent"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

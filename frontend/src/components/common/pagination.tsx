import { ChevronLeft, ChevronRight } from "lucide-react";
import type { Pagination } from "@/types/api";

interface PaginationControlsProps {
  pagination: Pagination | null;
  onPageChange: (page: number) => void;
}

function getPageNumbers(current: number, total: number): (number | "...")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages: (number | "...")[] = [1];
  if (current > 3) pages.push("...");
  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);
  for (let i = start; i <= end; i++) pages.push(i);
  if (current < total - 2) pages.push("...");
  pages.push(total);
  return pages;
}

export function PaginationControls({ pagination, onPageChange }: PaginationControlsProps) {
  if (!pagination) return null;
  const { page, total_pages, total } = pagination;
  const pages = getPageNumbers(page, total_pages);

  return (
    <div className="flex items-center justify-between border-t border-border py-3">
      <p className="text-sm text-muted-foreground">
        {total} result{total !== 1 ? "s" : ""} &middot; Page {page} of {total_pages}
      </p>
      {total_pages > 1 && (
        <div className="flex items-center gap-1">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-border text-sm disabled:opacity-30 hover:bg-accent disabled:hover:bg-transparent"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          {pages.map((p, i) =>
            p === "..." ? (
              <span key={`ellipsis-${i}`} className="flex h-8 w-8 items-center justify-center text-sm text-muted-foreground">
                ...
              </span>
            ) : (
              <button
                key={p}
                onClick={() => onPageChange(p)}
                className={`flex h-8 w-8 items-center justify-center rounded-md text-sm ${
                  p === page
                    ? "bg-primary text-primary-foreground"
                    : "border border-border hover:bg-accent"
                }`}
              >
                {p}
              </button>
            ),
          )}
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= total_pages}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-border text-sm disabled:opacity-30 hover:bg-accent disabled:hover:bg-transparent"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
import { useState, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Plus } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/common/data-table";
import { PaginationControls } from "@/components/common/pagination";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { EmptyState } from "@/components/common/empty-state";
import { StatusBadge } from "@/components/common/status-badge";
import { SearchInput } from "@/components/common/search-input";
import { FilterBar } from "@/components/common/filter-bar";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useTasks, useDeleteTask } from "@/api/tasks";
import type { Task } from "@/types/cmms";

export default function TasksPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [taskTypeFilter, setTaskTypeFilter] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Task | null>(null);

  const { data, isLoading, isError, error, refetch } = useTasks({
    page,
    per_page: 20,
    status: statusFilter || undefined,
    task_type: taskTypeFilter || undefined,
  });

  const deleteMutation = useDeleteTask();

  const onSearchChange = useCallback((v: string) => setSearch(v), []);

  const filtered = data?.data.filter(
    (t) => !search || t.name.toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <><PageHeader title="Tasks" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Tasks" /><ErrorState message={error.message} onRetry={() => refetch()} /></>;

  return (
    <>
      <PageHeader
        title="Tasks"
        description="Manage maintenance and operational tasks"
        actions={
          <Link
            to="/tasks/new"
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Task
          </Link>
        }
      />
      <FilterBar>
        <SearchInput value={search} onChange={onSearchChange} placeholder="Search tasks..." />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select
          value={taskTypeFilter}
          onChange={(e) => { setTaskTypeFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All types</option>
          <option value="general">General</option>
          <option value="inspection">Inspection</option>
          <option value="repair">Repair</option>
          <option value="installation">Installation</option>
          <option value="calibration">Calibration</option>
        </select>
      </FilterBar>

      {filtered && filtered.length > 0 ? (
        <>
          <DataTable<Task>
            data={filtered}
            keyExtractor={(t) => t.id}
            onRowClick={(t) => navigate(`/tasks/${t.id}`)}
            columns={[
              { header: "Name", accessor: "name" },
              { header: "Type", accessor: "task_type" },
              { header: "Status", accessor: (t) => <StatusBadge value={t.status} /> },
              { header: "Estimated Duration", accessor: (t) => t.estimated_duration_hours != null ? `${t.estimated_duration_hours}h` : "-" },
              {
                header: "Actions",
                accessor: (t) => (
                  <button
                    onClick={(e) => { e.stopPropagation(); setDeleteTarget(t); }}
                    className="text-xs text-destructive hover:underline"
                  >
                    Delete
                  </button>
                ),
              },
            ]}
          />
          <PaginationControls pagination={data?.pagination ?? null} onPageChange={setPage} />
        </>
      ) : (
        <EmptyState title="No tasks found" description="Create your first task to get started." action={
          <Link to="/tasks/new" className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground">Create Task</Link>
        } />
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Task"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.`}
        variant="destructive"
        confirmLabel="Delete"
        onConfirm={() => {
          if (deleteTarget) deleteMutation.mutate(deleteTarget.id);
          setDeleteTarget(null);
        }}
        onCancel={() => setDeleteTarget(null)}
      />
    </>
  );
}

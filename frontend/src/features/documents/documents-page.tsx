import { useState } from "react";
import { Trash2, FileText } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { DataTable } from "@/components/common/data-table";
import { LoadingState } from "@/components/common/loading-state";
import { ErrorState } from "@/components/common/error-state";
import { EmptyState } from "@/components/common/empty-state";
import { FileUpload } from "@/components/common/file-upload";
import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { useDocuments, useUploadDocument, useDeleteDocument } from "@/api/documents";
import type { DocumentInfo } from "@/types/document";

export default function DocumentsPage() {
  const [deleteTarget, setDeleteTarget] = useState<DocumentInfo | null>(null);
  const { data, isLoading, isError, error, refetch } = useDocuments({ per_page: 50 });
  const uploadMutation = useUploadDocument();
  const deleteMutation = useDeleteDocument();

  if (isLoading) return <><PageHeader title="Documents" /><LoadingState /></>;
  if (isError) return <><PageHeader title="Documents" /><ErrorState message={error?.message} onRetry={() => refetch()} /></>;

  const documents = data?.documents ?? [];

  return (
    <>
      <PageHeader title="Documents" description="Upload and manage knowledge base documents" />

      <div className="mb-6">
        <FileUpload
          onFiles={(files) => {
            uploadMutation.mutate({ file: files[0] });
          }}
          accept={{ "application/pdf": [".pdf"], "text/plain": [".txt"], "text/markdown": [".md"] }}
        />
        {uploadMutation.isPending && <p className="mt-2 text-sm text-muted-foreground">Uploading...</p>}
        {uploadMutation.isError && <p className="mt-2 text-sm text-destructive">{uploadMutation.error.message}</p>}
      </div>

      {documents.length > 0 ? (
        <DataTable<DocumentInfo>
          data={documents}
          keyExtractor={(d) => d.document_id}
          columns={[
            {
              header: "Filename",
              accessor: (d) => (
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span>{d.filename}</span>
                </div>
              ),
            },
            { header: "Title", accessor: (d) => d.title ?? "-" },
            { header: "Chunks", accessor: (d) => d.chunks_count },
            {
              header: "Actions",
              accessor: (d) => (
                <button onClick={() => setDeleteTarget(d)} className="flex items-center gap-1 text-xs text-destructive hover:underline">
                  <Trash2 className="h-3.5 w-3.5" /> Delete
                </button>
              ),
            },
          ]}
        />
      ) : (
        <EmptyState title="No documents" description="Upload your first document to get started." />
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Document"
        description={`Delete "${deleteTarget?.filename}"? This will remove it from the knowledge base.`}
        variant="destructive"
        confirmLabel="Delete"
        onConfirm={() => {
          if (deleteTarget) deleteMutation.mutate(deleteTarget.document_id);
          setDeleteTarget(null);
        }}
        onCancel={() => setDeleteTarget(null)}
      />
    </>
  );
}

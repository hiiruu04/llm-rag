import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { DocumentInfo } from "@/types/document";

export function useDocuments(params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ["documents", params],
    queryFn: async () => {
      const res = await apiClient.get<{ documents: DocumentInfo[] }>("/api/v1/documents", { params });
      const pagination = res.headers["x-pagination"];
      return {
        documents: res.data.documents,
        pagination: pagination ? JSON.parse(pagination as string) : null,
      };
    },
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, title, tags, author }: { file: File; title?: string; tags?: string[]; author?: string }) => {
      const form = new FormData();
      form.append("file", file);
      if (title) form.append("title", title);
      if (tags) form.append("tags", tags.join(","));
      if (author) form.append("author", author);
      return apiClient.post("/api/v1/documents", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (documentId: string) => apiClient.delete(`/api/v1/documents/${documentId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor: unwrap the { data, meta } envelope
apiClient.interceptors.response.use(
  (response) => {
    const envelope = response.data;
    if (envelope && typeof envelope === "object" && "data" in envelope && "meta" in envelope) {
      const pagination = envelope.meta?.pagination ?? null;
      if (pagination) {
        response.headers["x-pagination"] = JSON.stringify(pagination);
      }
      response.data = envelope.data;
    }
    return response;
  },
  (error) => {
    const message =
      error.response?.data?.meta?.details ||
      error.response?.data?.detail ||
      error.message ||
      "An unexpected error occurred";
    return Promise.reject(new Error(message));
  },
);

export interface PaginationInfo {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export function extractPagination(response: { headers: Record<string, unknown> }): PaginationInfo | null {
  const raw = response.headers["x-pagination"];
  if (!raw || typeof raw !== "string") return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export async function paginatedGet<T>(url: string, params?: Record<string, unknown>) {
  const res = await apiClient.get(url, { params });
  return {
    data: res.data as T[],
    pagination: extractPagination(res),
  };
}

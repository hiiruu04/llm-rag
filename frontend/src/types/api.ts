export interface ApiResponse<T> {
  data: T;
  meta: Meta;
}

export interface Meta {
  status_code: number;
  details?: string;
  errors?: string[];
  pagination?: Pagination;
}

export interface Pagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

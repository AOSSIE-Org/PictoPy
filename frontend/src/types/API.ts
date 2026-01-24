export interface APIResponse {
  data?: {
    [key: string]: any;
  };
  success: boolean;
  error?: string;
  message?: string;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total_count: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PaginatedAPIResponse<T> {
  data: T[];
  success: boolean;
  message?: string;
  error?: string;
  pagination: PaginationInfo;
}

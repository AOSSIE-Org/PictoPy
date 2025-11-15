export interface APIResponse<T = any> {
  data?: T;
  success: boolean;
  error?: string;
  message?: string;
  total?: number;
  limit?: number;
  offset?: number;
}

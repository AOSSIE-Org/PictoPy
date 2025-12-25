export interface APIResponse<T = Record<string, unknown>> {
  data?: T;
  success: boolean;
  error?: string;
  message?: string;
}

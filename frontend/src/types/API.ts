export interface APIResponse {
  data?: {
    [key: string]: any;
  };
  success: boolean;
  error?: string;
  message?: string;
}

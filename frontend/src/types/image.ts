export interface Image {
  title: string;
  url: string;
  tags: any;
  thumbnailUrl: string;
}

export interface APIResponse {
  data: {
    [key: string]: any;
  };
  success: boolean;
  error?: string;
  message?: string;
}

export type JobId = string;

export interface ApiJob {
  jobId: JobId;
  percent: number;
  processed?: number;
  total?: number;
  status?: string;
  seq?: number | null;
  ts?: number | null; // epoch ms
}

export interface WsProgressMessage {
  type: 'progress';
  seq: number;
  ts: number;
  payload: {
    job_id: JobId;
    processed: number;
    total: number;
    percent: number;
    status: string;
  };
}

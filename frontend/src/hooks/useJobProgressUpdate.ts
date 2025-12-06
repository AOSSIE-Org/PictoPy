// useJobProgressUpdate.ts
import type { ApiJob, JobId, WsProgressMessage } from "../types/FolderProgress";
import { Dispatch, SetStateAction } from "react";

export type MetaStore = Record<JobId, { seq: number | null; ts: number }>;

export function applyIfNewerFromWs(
  msg: WsProgressMessage,
  metaRef: React.MutableRefObject<MetaStore>,
  setJobs: Dispatch<SetStateAction<Record<JobId, ApiJob>>>
) {
  const payload = msg.payload;
  const jobId = payload.job_id;
  if (!jobId) return;

  const incomingSeq = typeof msg.seq === "number" ? msg.seq : null;
  const incomingTs = typeof msg.ts === "number" ? msg.ts : Date.now();

  const existing = metaRef.current[jobId] ?? { seq: null, ts: 0 };

  let accept = false;
  if (incomingSeq !== null && existing.seq !== null) {
    accept = incomingSeq > existing.seq;
  } else if (incomingSeq !== null && existing.seq === null) {
    accept = true;
  } else {
    accept = incomingTs > existing.ts;
  }

  if (!accept) return;

  // update meta
  metaRef.current[jobId] = { seq: incomingSeq, ts: incomingTs };

  // update UI job map
  setJobs(prev => {
    const prevJob = prev[jobId] ?? {
      jobId,
      percent: payload.percent,
      processed: payload.processed,
      total: payload.total,
      status: payload.status,
      seq: incomingSeq,
      ts: incomingTs
    };

    const nextJob: ApiJob = {
      ...prevJob,
      percent: payload.percent ?? prevJob.percent,
      processed: payload.processed ?? prevJob.processed,
      total: payload.total ?? prevJob.total,
      status: payload.status ?? prevJob.status,
      seq: incomingSeq,
      ts: incomingTs
    };

    return { ...prev, [jobId]: nextJob };
  });
}

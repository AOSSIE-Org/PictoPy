import { useState, useEffect, useRef } from 'react';
import { BACKEND_URL } from '@/config/Backend';
import { ModelDownloadProgressMessage } from '@/types/models';

export type ProgressStatus = 'idle' | 'downloading' | 'complete' | 'error';

export interface UseModelDownloadProgressResult {
  status: ProgressStatus;
  percent: number; // Overall compound percent
  currentModelPercent: number; // Raw percent for the current model file
  downloaded: number;
  total: number;
  modelKey: string;
  modelIndex: number;
  totalModels: number;
  errorMsg: string;
}

export function useModelDownloadProgress(
  taskId: string | null,
): UseModelDownloadProgressResult {
  const [status, setStatus] = useState<ProgressStatus>('idle');
  const [percent, setPercent] = useState(0);
  const [currentModelPercent, setCurrentModelPercent] = useState(0);
  const [downloaded, setDownloaded] = useState(0);
  const [total, setTotal] = useState(0);
  const [modelKey, setModelKey] = useState('');
  const [modelIndex, setModelIndex] = useState(0);
  const [totalModels, setTotalModels] = useState(0);
  const [errorMsg, setErrorMsg] = useState('');

  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!taskId) {
      setStatus('idle');
      setPercent(0);
      setCurrentModelPercent(0);
      setDownloaded(0);
      setTotal(0);
      setModelKey('');
      setModelIndex(0);
      setTotalModels(0);
      setErrorMsg('');
      return;
    }

    setStatus('downloading');
    setPercent(0);
    setCurrentModelPercent(0);
    setErrorMsg('');

    const source = new EventSource(
      `${BACKEND_URL}/models/download/${taskId}/progress`,
    );
    eventSourceRef.current = source;

    source.onmessage = (event) => {
      try {
        const msg: ModelDownloadProgressMessage = JSON.parse(event.data);

        if (msg.status === 'downloading') {
          setStatus('downloading');
          const pPerModel = 100 / msg.total_models;
          const basePercent = (msg.model_index - 1) * pPerModel;
          const cModelPercent = (msg.percent / 100) * pPerModel;

          setPercent(Math.min(100, Math.round(basePercent + cModelPercent)));
          setCurrentModelPercent(msg.percent);
          setDownloaded(msg.downloaded);
          setTotal(msg.total);
          setModelKey(msg.model_key);
          setModelIndex(msg.model_index);
          setTotalModels(msg.total_models);
        } else if (msg.status === 'complete') {
          setStatus('complete');
          setPercent(100);
          source.close();
        } else if (msg.status === 'error') {
          setStatus('error');
          setErrorMsg(msg.message || 'Download failed');
          source.close();
        }
      } catch (err) {
        console.error('Malformed SSE payload', err);
        setStatus('error');
        setErrorMsg(
          'Received malformed download progress data. Please try again.',
        );
        source.close();
      }
    };

    source.onerror = (err) => {
      console.error('SSE Error', err);
      setStatus('error');
      setErrorMsg('Connection lost during download. Please try again.');
      source.close();
    };

    return () => {
      source.close();
    };
  }, [taskId]);

  return {
    status,
    percent,
    currentModelPercent,
    downloaded,
    total,
    modelKey,
    modelIndex,
    totalModels,
    errorMsg,
  };
}

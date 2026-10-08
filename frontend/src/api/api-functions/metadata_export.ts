import { metadataExportEndpoints } from '../apiEndpoints';
import { apiClient } from '../axiosConfig';
import { APIResponse } from '@/types/API';

/** What one export pass did. */
export interface ExportRunSummary {
  checked: number;
  written: number;
  unchanged: number;
  /** Nothing to store, unreadable existing metadata, or a newer PictoPy's data. */
  skipped: number;
  failed: number;
}

export interface MetadataExportStatus {
  /** PNG images only: the one format PictoPy can write metadata into today. */
  total: number;
  pending: number;
  /** Pending images whose last write failed; the next pass retries them. */
  failed: number;
  /** Left alone on purpose: unreadable existing metadata or a newer PictoPy's. */
  skipped: number;
  /** The export started from Settings, not one a sync runs itself. */
  running: boolean;
  run_failed: boolean;
  last_run: ExportRunSummary | null;
}

export interface MetadataExportStatusResponse extends APIResponse {
  data: MetadataExportStatus;
}

/** Starts a library-wide export in the background; returns its starting point. */
export const startMetadataExport =
  async (): Promise<MetadataExportStatusResponse> => {
    const response = await apiClient.post<MetadataExportStatusResponse>(
      metadataExportEndpoints.run,
    );
    return response.data;
  };

export const getMetadataExportStatus =
  async (): Promise<MetadataExportStatusResponse> => {
    const response = await apiClient.get<MetadataExportStatusResponse>(
      metadataExportEndpoints.status,
    );
    return response.data;
  };

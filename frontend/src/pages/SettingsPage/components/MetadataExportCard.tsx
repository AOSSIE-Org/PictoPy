import React, { useCallback, useState } from 'react';
import { FileImage, Save } from 'lucide-react';

import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { useUserPreferences } from '@/hooks/useUserPreferences';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import {
  getMetadataExportStatus,
  startMetadataExport,
  type MetadataExportStatus,
} from '@/api/api-functions';
import SettingsCard from './SettingsCard';

/** One line saying where the library stands, for the Export row. */
export const describeExportStatus = (
  status: MetadataExportStatus | undefined,
): string => {
  if (!status) return 'Checking your library…';
  const { total, pending, failed, skipped } = status;
  if (total === 0) {
    return 'No PNG images in your library yet. Only PNG files are supported for now.';
  }
  if (status.running) {
    return `Saving metadata — ${pending} of ${total} PNG images left. This keeps going in the background.`;
  }

  let line = status.run_failed
    ? `The last export stopped with an error. ${pending} PNG image(s) still need their metadata saved.`
    : pending === 0
      ? `All ${total} PNG images hold up-to-date metadata.`
      : `${pending} of ${total} PNG images need their metadata saved.`;
  if (failed > 0) {
    line += ` ${failed} couldn't be written last time and will be retried.`;
  }
  if (skipped > 0) {
    line += ` ${skipped} were left alone because their existing metadata couldn't be read.`;
  }
  return line;
};

/**
 * Writing PictoPy's tags, faces and embeddings into the image files, so a
 * reinstall can reuse them instead of running the AI again.
 */
const MetadataExportCard: React.FC = () => {
  const { preferences, toggleMetadataExport } = useUserPreferences();
  const [starting, setStarting] = useState(false);

  // Counted in the database, so automatic passes show up here as well.
  const statusQuery = usePictoQuery({
    queryKey: ['metadata-export', 'status'],
    queryFn: getMetadataExportStatus,
    refetchInterval: (query) => {
      const data = query.state.data?.data;
      if (data?.running) return 2000;
      // Automatic passes aren't tracked as running; check back now and then.
      return preferences.Metadata_Export && (data?.pending ?? 0) > 0
        ? 10000
        : false;
    },
    refetchIntervalInBackground: true,
  });
  const status = statusQuery.successData;
  const running = status?.running ?? false;

  const handleExport = useCallback(async () => {
    setStarting(true);
    try {
      await startMetadataExport();
    } catch (err) {
      console.error('Failed to start the metadata export', err);
    }
    await statusQuery.refetch();
    setStarting(false);
  }, [statusQuery]);

  return (
    <SettingsCard
      icon={FileImage}
      title="Image Metadata"
      description="Keep PictoPy's work inside your photos"
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Label
              htmlFor="metadata-export"
              className="text-foreground text-sm font-medium"
            >
              Save Metadata Automatically
            </Label>
            <p className="text-muted-foreground text-xs">
              After tagging, and when you edit favourites, albums or people,
              write tags, faces and embeddings into your PNG files so a
              reinstall can reuse them. Pixels and file dates are not changed.
            </p>
          </div>
          <Switch
            className="cursor-pointer"
            id="metadata-export"
            checked={preferences.Metadata_Export}
            onCheckedChange={() => toggleMetadataExport().catch(console.warn)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Label className="text-foreground text-sm font-medium">
              Export Now
            </Label>
            <p className="text-muted-foreground text-xs">
              {describeExportStatus(status)}
            </p>
          </div>
          <Button
            variant="outline"
            className="cursor-pointer"
            disabled={starting || running || (status?.total ?? 0) === 0}
            onClick={handleExport}
          >
            <Save className="mr-2 h-4 w-4" />
            {running || starting
              ? 'Exporting...'
              : status?.run_failed
                ? 'Retry export'
                : 'Export metadata'}
          </Button>
        </div>

        <p className="text-muted-foreground text-xs">
          Photos shared by link never include this data.
        </p>
      </div>
    </SettingsCard>
  );
};

export default MetadataExportCard;

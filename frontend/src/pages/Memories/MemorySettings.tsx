import React from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/Slider';
import { useUserPreferences } from '@/hooks/useUserPreferences';
import type { MemoriesPreferences } from '@/api/api-functions/user_preferences';

interface ToggleRowProps {
  id: string;
  label: string;
  description: string;
  checked: boolean;
  disabled?: boolean;
  onChange: (checked: boolean) => void;
}

const ToggleRow: React.FC<ToggleRowProps> = ({
  id,
  label,
  description,
  checked,
  disabled,
  onChange,
}) => (
  <div className="flex items-start justify-between gap-6 py-4">
    <div className="min-w-0">
      <Label htmlFor={id} className="text-sm font-medium">
        {label}
      </Label>
      <p className="text-muted-foreground mt-1 text-sm">{description}</p>
    </div>
    <Switch
      id={id}
      checked={checked}
      disabled={disabled}
      onCheckedChange={onChange}
    />
  </div>
);

export const MemorySettings: React.FC = () => {
  const navigate = useNavigate();
  const { memoriesPreferences, updateMemoriesPreferences, isUpdating } =
    useUserPreferences();

  const patch = (update: Partial<MemoriesPreferences>) => {
    void updateMemoriesPreferences(update).catch(() => undefined);
  };

  return (
    <div className="hide-scrollbar h-full overflow-y-auto p-6">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(-1)}
            aria-label="Go back"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-2xl font-bold">Memory settings</h1>
        </div>

        <Card className="mb-4 px-5 py-1">
          <ToggleRow
            id="memories-enabled"
            label="Generate memories"
            description="Curate highlights from your library automatically."
            checked={memoriesPreferences.enabled}
            disabled={isUpdating}
            onChange={(checked) => patch({ enabled: checked })}
          />
          <div className="bg-border h-px" />
          <ToggleRow
            id="memories-notifications"
            label="Desktop notifications"
            description="Get an alert when a new memory is ready."
            checked={memoriesPreferences.notifications_enabled}
            disabled={isUpdating || !memoriesPreferences.enabled}
            onChange={(checked) => patch({ notifications_enabled: checked })}
          />
        </Card>

        <Card className="mb-4 px-5 py-1">
          <ToggleRow
            id="memories-music"
            label="Background music"
            description="Play a soundtrack while a memory is showing. Off by default."
            checked={memoriesPreferences.story_music_enabled}
            disabled={isUpdating}
            onChange={(checked) => patch({ story_music_enabled: checked })}
          />
          <div className="bg-border h-px" />
          <div className="py-4">
            <div className="flex items-center justify-between gap-6">
              <Label
                htmlFor="memories-duration"
                className="text-sm font-medium"
              >
                Seconds per photo
              </Label>
              <span className="text-muted-foreground text-sm tabular-nums">
                {memoriesPreferences.slide_duration_seconds}s
              </span>
            </div>
            <p className="text-muted-foreground mt-1 mb-3 text-sm">
              How long each photo is held before the story advances.
            </p>
            <Slider
              id="memories-duration"
              min={1}
              max={15}
              step={1}
              value={[memoriesPreferences.slide_duration_seconds]}
              disabled={isUpdating}
              onValueCommit={([value]) =>
                patch({ slide_duration_seconds: value })
              }
            />
          </div>
        </Card>

        <Card className="px-5 py-1">
          <div className="py-4">
            <Label className="text-sm font-medium">Memory size</Label>
            <p className="text-muted-foreground mt-1 text-sm">
              Memories with fewer than {memoriesPreferences.min_images} photos
              are skipped, and no memory shows more than{' '}
              {memoriesPreferences.max_images}.
            </p>
          </div>
          <div className="bg-border h-px" />
          <div className="py-4">
            <div className="flex items-center justify-between gap-6">
              <Label htmlFor="memories-min" className="text-sm">
                Minimum photos
              </Label>
              <span className="text-muted-foreground text-sm tabular-nums">
                {memoriesPreferences.min_images}
              </span>
            </div>
            <Slider
              id="memories-min"
              className="mt-3"
              min={2}
              max={20}
              step={1}
              value={[memoriesPreferences.min_images]}
              disabled={isUpdating}
              onValueCommit={([value]) =>
                patch({
                  min_images: value,
                  // Keep the pair valid: the backend rejects a minimum above
                  // the maximum, which would fail the whole save.
                  max_images: Math.max(value, memoriesPreferences.max_images),
                })
              }
            />
          </div>
          <div className="py-4">
            <div className="flex items-center justify-between gap-6">
              <Label htmlFor="memories-max" className="text-sm">
                Maximum photos
              </Label>
              <span className="text-muted-foreground text-sm tabular-nums">
                {memoriesPreferences.max_images}
              </span>
            </div>
            <Slider
              id="memories-max"
              className="mt-3"
              min={5}
              max={100}
              step={5}
              value={[memoriesPreferences.max_images]}
              disabled={isUpdating}
              onValueCommit={([value]) =>
                patch({
                  max_images: value,
                  min_images: Math.min(value, memoriesPreferences.min_images),
                })
              }
            />
          </div>
        </Card>
      </div>
    </div>
  );
};

export default MemorySettings;

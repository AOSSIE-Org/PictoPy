import React, { useEffect, useCallback, useState } from 'react';
import {
  Cpu,
  ChevronDown,
  Zap,
  Trash2,
  Clapperboard,
  HardDrive,
  Sparkles,
  Bell,
} from 'lucide-react';

import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { getCurrentWindow } from '@tauri-apps/api/window';

import { useUserPreferences } from '@/hooks/useUserPreferences';
import type { UpdateUserPreferencesRequest } from '@/api/api-functions/user_preferences';
import { purgeVideoFrameCache } from '@/api/api-functions';
import SettingsCard from './SettingsCard';
import { cn, formatTierLabel } from '@/lib/utils';
import { BACKEND_URL } from '@/config/Backend';
import {
  getInstalledModelTiers,
  MODEL_TIERS,
  type ModelStatusResponse,
  type ModelTier,
} from '@/types/models';

// Coarse enough to be a meaningful cost tradeoff, fine enough to matter.
const FRAME_INTERVAL_OPTIONS = [2, 5, 10, 30];
// Story pacing: below 3s a photo barely registers, above 10s it drags.
const SLIDE_DURATION_OPTIONS = [3, 5, 7, 10];
const MIN_IMAGE_OPTIONS = [3, 5, 8, 10];
const MAX_IMAGE_OPTIONS = [20, 30, 50, 100];

const UserPreferencesCard: React.FC = () => {
  const {
    preferences,
    memoriesPreferences,
    updateYoloModelSize,
    toggleGpuAcceleration,
    updateVideoFrameInterval,
    updateMemoriesPreferences,
    isUpdating,
    refetch,
  } = useUserPreferences();
  const [installedTiers, setInstalledTiers] = useState<ModelTier[]>([]);
  const [loadingTiers, setLoadingTiers] = useState(true);
  const [tierFetchError, setTierFetchError] = useState<string | null>(null);
  const [purgeState, setPurgeState] = useState<'idle' | 'purging' | 'done'>(
    'idle',
  );
  // Collapsed by default: video tagging is a niche setting, so it stays out
  // of the way until a user with videos goes looking for it.
  const [videoSettingsOpen, setVideoSettingsOpen] = useState(false);
  const [memorySettingsOpen, setMemorySettingsOpen] = useState(false);

  const patchMemories = useCallback(
    (update: UpdateUserPreferencesRequest['memories']) => {
      void updateMemoriesPreferences(update).catch(console.warn);
    },
    [updateMemoriesPreferences],
  );

  const handlePurgeFrameCache = useCallback(async () => {
    setPurgeState('purging');
    try {
      await purgeVideoFrameCache();
      setPurgeState('done');
    } catch (err) {
      console.error('Failed to purge video frame cache', err);
      setPurgeState('idle');
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    const fetchModelStatus = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/models/status`, {
          signal: controller.signal,
        });

        if (!res.ok) {
          throw new Error(`Failed to load models (${res.status})`);
        }

        const data: ModelStatusResponse = await res.json();

        if (controller.signal.aborted) {
          return;
        }

        if (data.success && data.data) {
          setInstalledTiers(getInstalledModelTiers(data.data));
          setTierFetchError(null);
        } else {
          setTierFetchError('Failed to load models');
        }
      } catch (err) {
        if (controller.signal.aborted) {
          return;
        }

        console.error('Failed to fetch model status', err);
        setTierFetchError(
          err instanceof Error ? err.message : 'Failed to load models',
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoadingTiers(false);
        }
      }
    };

    fetchModelStatus();

    return () => {
      controller.abort();
    };
  }, []);

  // Model Manager emits 'models-updated' on close to refresh installed-tiers and active preference.
  const refreshAfterModelManager = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/models/status`);
      if (res.ok) {
        const data: ModelStatusResponse = await res.json();
        if (data.success && data.data) {
          setInstalledTiers(getInstalledModelTiers(data.data));
        }
      }
    } catch (err) {
      console.error('Failed to refresh model status', err);
    }
    refetch().catch(console.error);
  }, [refetch]);

  useEffect(() => {
    const unlistenModelsPromise = listen(
      'models-updated',
      refreshAfterModelManager,
    );
    const unlistenFocusPromise = getCurrentWindow().onFocusChanged(
      ({ payload: focused }) => {
        if (focused) {
          refreshAfterModelManager();
        }
      },
    );

    return () => {
      unlistenModelsPromise.then((unlisten) => unlisten());
      unlistenFocusPromise.then((unlisten) => unlisten());
    };
  }, [refreshAfterModelManager]);

  return (
    <SettingsCard
      icon={Cpu}
      title="User Preferences"
      description="Configure AI model settings and performance options"
    >
      <div className="space-y-6">
        {/* YOLO Model Size Setting */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Label
              htmlFor="yolo-model"
              className="text-foreground text-sm font-medium"
            >
              YOLO Model Size
            </Label>
            <p className="text-muted-foreground text-xs">
              Choose the AI model size for object detection (larger models are
              more accurate but slower)
            </p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="w-32 cursor-pointer justify-between"
              >
                {formatTierLabel(preferences.YOLO_model_size)}
                <ChevronDown className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-32">
              {MODEL_TIERS.map((tier) =>
                installedTiers.includes(tier) ? (
                  <DropdownMenuItem
                    key={tier}
                    className="cursor-pointer"
                    onClick={() =>
                      updateYoloModelSize(tier).catch(console.warn)
                    }
                  >
                    {formatTierLabel(tier)}
                  </DropdownMenuItem>
                ) : null,
              )}
              {loadingTiers && (
                <DropdownMenuItem disabled>Loading models...</DropdownMenuItem>
              )}
              {!loadingTiers && tierFetchError && (
                <DropdownMenuItem disabled>
                  Failed to load models
                </DropdownMenuItem>
              )}
              {!loadingTiers &&
                !tierFetchError &&
                installedTiers.length === 0 && (
                  <DropdownMenuItem disabled>
                    No models installed
                  </DropdownMenuItem>
                )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="hover:text-secondary cursor-pointer font-medium"
                onSelect={() => {
                  invoke('open_model_manager').catch(console.error);
                }}
              >
                Configure...
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* GPU Acceleration Setting */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Label
              htmlFor="gpu-acceleration"
              className="text-foreground text-sm font-medium"
            >
              GPU Acceleration
            </Label>
            <p className="text-muted-foreground text-xs">
              Enable GPU acceleration for faster AI processing (requires
              compatible hardware)
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-gray-500" />
            <Switch
              className="cursor-pointer"
              id="gpu-acceleration"
              checked={preferences.GPU_Acceleration}
              onCheckedChange={() =>
                toggleGpuAcceleration().catch(console.warn)
              }
            />
          </div>
        </div>

        {/* Video Tagging: a collapsible group so these niche controls don't
            clutter the panel for users who only have photos. */}
        <div className="border-border rounded-lg border">
          <button
            type="button"
            aria-expanded={videoSettingsOpen}
            aria-controls="video-tagging-settings"
            onClick={() => setVideoSettingsOpen((open) => !open)}
            className="flex w-full cursor-pointer items-center justify-between gap-3 rounded-lg p-4 text-left transition-colors"
          >
            <div className="flex items-start gap-3">
              <Clapperboard className="text-muted-foreground mt-0.5 h-5 w-5 shrink-0" />
              <div className="space-y-1">
                <span className="text-foreground text-sm font-medium">
                  Video Tagging
                </span>
                <p className="text-muted-foreground text-xs">
                  Control how videos are sampled for AI tags and manage the
                  frames cached on disk.
                </p>
              </div>
            </div>
            <ChevronDown
              className={cn(
                'text-muted-foreground h-4 w-4 shrink-0 transition-transform',
                videoSettingsOpen && 'rotate-180',
              )}
            />
          </button>

          {videoSettingsOpen && (
            <div
              id="video-tagging-settings"
              className="border-border space-y-6 border-t p-4"
            >
              {/* Video Keyframe Interval Setting */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label
                    htmlFor="video-frame-interval"
                    className="text-foreground text-sm font-medium"
                  >
                    Keyframe Interval
                  </Label>
                  <p className="text-muted-foreground text-xs">
                    How often a frame is sampled from a video for tagging.
                    Shorter intervals catch more detail but take longer to
                    process. Applies to videos tagged from now on.
                  </p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="outline"
                      className="w-32 cursor-pointer justify-between"
                    >
                      {preferences.Video_Frame_Interval}s
                      <ChevronDown className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-32">
                    {FRAME_INTERVAL_OPTIONS.map((seconds) => (
                      <DropdownMenuItem
                        key={seconds}
                        className="cursor-pointer"
                        onClick={() =>
                          updateVideoFrameInterval(seconds).catch(console.warn)
                        }
                      >
                        {seconds} seconds
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Video Frame Cache */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label className="text-foreground text-sm font-medium">
                    Frame Cache
                  </Label>
                  <p className="text-muted-foreground text-xs">
                    Reclaim the disk space used by sampled video frames.
                    Existing tags and video search keep working.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <HardDrive className="h-4 w-4 text-gray-500" />
                  <Button
                    variant="outline"
                    className="cursor-pointer"
                    disabled={purgeState === 'purging'}
                    onClick={handlePurgeFrameCache}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    {purgeState === 'purging'
                      ? 'Clearing...'
                      : purgeState === 'done'
                        ? 'Cleared'
                        : 'Clear cache'}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Memories: same collapsible treatment as video tagging, so the
            two niche groups read as siblings. */}
        <div className="border-border rounded-lg border">
          <button
            type="button"
            aria-expanded={memorySettingsOpen}
            aria-controls="memories-settings"
            onClick={() => setMemorySettingsOpen((open) => !open)}
            className="flex w-full cursor-pointer items-center justify-between gap-3 rounded-lg p-4 text-left transition-colors"
          >
            <div className="flex items-start gap-3">
              <Sparkles className="text-muted-foreground mt-0.5 h-5 w-5 shrink-0" />
              <div className="space-y-1">
                <span className="text-foreground text-sm font-medium">
                  Memories
                </span>
                <p className="text-muted-foreground text-xs">
                  Control how memories are generated, delivered and paced.
                </p>
              </div>
            </div>
            <ChevronDown
              className={cn(
                'text-muted-foreground h-4 w-4 shrink-0 transition-transform',
                memorySettingsOpen && 'rotate-180',
              )}
            />
          </button>

          {memorySettingsOpen && (
            <div
              id="memories-settings"
              className="border-border space-y-6 border-t p-4"
            >
              {/* Generate Memories Setting */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label
                    htmlFor="memories-enabled"
                    className="text-foreground text-sm font-medium"
                  >
                    Generate Memories
                  </Label>
                  <p className="text-muted-foreground text-xs">
                    Curate highlights from your library automatically.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-gray-500" />
                  <Switch
                    className="cursor-pointer"
                    id="memories-enabled"
                    checked={memoriesPreferences.enabled}
                    disabled={isUpdating}
                    onCheckedChange={(checked) =>
                      patchMemories({ enabled: checked })
                    }
                  />
                </div>
              </div>

              {/* Desktop Notifications Setting */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label
                    htmlFor="memories-notifications"
                    className="text-foreground text-sm font-medium"
                  >
                    Desktop Notifications
                  </Label>
                  <p className="text-muted-foreground text-xs">
                    Get an alert when a new memory is ready.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Bell className="h-4 w-4 text-gray-500" />
                  <Switch
                    className="cursor-pointer"
                    id="memories-notifications"
                    checked={memoriesPreferences.notifications_enabled}
                    disabled={isUpdating || !memoriesPreferences.enabled}
                    onCheckedChange={(checked) =>
                      patchMemories({ notifications_enabled: checked })
                    }
                  />
                </div>
              </div>

              {/* Seconds Per Photo Setting */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label
                    htmlFor="memories-duration"
                    className="text-foreground text-sm font-medium"
                  >
                    Seconds Per Photo
                  </Label>
                  <p className="text-muted-foreground text-xs">
                    How long each photo is held before the story advances. A
                    video clip runs for its own length instead.
                  </p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      id="memories-duration"
                      variant="outline"
                      className="w-32 cursor-pointer justify-between"
                      disabled={isUpdating}
                    >
                      {memoriesPreferences.slide_duration_seconds}s
                      <ChevronDown className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-32">
                    {SLIDE_DURATION_OPTIONS.map((seconds) => (
                      <DropdownMenuItem
                        key={seconds}
                        className="cursor-pointer"
                        onClick={() =>
                          patchMemories({ slide_duration_seconds: seconds })
                        }
                      >
                        {seconds} seconds
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Minimum Photos Setting */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label
                    htmlFor="memories-min"
                    className="text-foreground text-sm font-medium"
                  >
                    Minimum Photos
                  </Label>
                  <p className="text-muted-foreground text-xs">
                    Groups with fewer photos than this are skipped rather than
                    turned into a memory.
                  </p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      id="memories-min"
                      variant="outline"
                      className="w-32 cursor-pointer justify-between"
                      disabled={isUpdating}
                    >
                      {memoriesPreferences.min_images} photos
                      <ChevronDown className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-32">
                    {MIN_IMAGE_OPTIONS.map((count) => (
                      <DropdownMenuItem
                        key={count}
                        className="cursor-pointer"
                        onClick={() =>
                          patchMemories({
                            min_images: count,
                            // Keep the pair valid: the backend rejects a
                            // minimum above the maximum, failing the save.
                            max_images: Math.max(
                              count,
                              memoriesPreferences.max_images,
                            ),
                          })
                        }
                      >
                        {count} photos
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Maximum Photos Setting */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label
                    htmlFor="memories-max"
                    className="text-foreground text-sm font-medium"
                  >
                    Maximum Photos
                  </Label>
                  <p className="text-muted-foreground text-xs">
                    No memory shows more photos than this, however many the
                    occasion produced.
                  </p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      id="memories-max"
                      variant="outline"
                      className="w-32 cursor-pointer justify-between"
                      disabled={isUpdating}
                    >
                      {memoriesPreferences.max_images} photos
                      <ChevronDown className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-32">
                    {MAX_IMAGE_OPTIONS.map((count) => (
                      <DropdownMenuItem
                        key={count}
                        className="cursor-pointer"
                        onClick={() =>
                          patchMemories({
                            max_images: count,
                            min_images: Math.min(
                              count,
                              memoriesPreferences.min_images,
                            ),
                          })
                        }
                      >
                        {count} photos
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          )}
        </div>
      </div>
    </SettingsCard>
  );
};

export default UserPreferencesCard;

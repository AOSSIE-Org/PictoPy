import React, { useEffect, useState } from 'react';
import { Cpu, ChevronDown, Zap } from 'lucide-react';

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


import { useUserPreferences } from '@/hooks/useUserPreferences';
import SettingsCard from './SettingsCard';
import { formatTierLabel } from '@/lib/utils';
import { BACKEND_URL } from '@/config/Backend';
import {
  getInstalledModelTiers,
  MODEL_TIERS,
  type ModelStatusResponse,
  type ModelTier,
} from '@/types/models';

/**
 * Component for managing user preferences in settings
 */
const UserPreferencesCard: React.FC = () => {
  const { preferences, updateYoloModelSize, toggleGpuAcceleration, refetch } =
    useUserPreferences();
  const [installedTiers, setInstalledTiers] = useState<ModelTier[]>([]);
  const [loadingTiers, setLoadingTiers] = useState(true);
  const [tierFetchError, setTierFetchError] = useState<string | null>(null);

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

  // ISSUE - 1369: Model Manager (isolated Tauri window) emits 'models-updated' on close; use it here to refresh installed-tiers and active preference.
  useEffect(() => {
    const unlistenPromise = listen('models-updated', async () => {
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
    });

    return () => {
      unlistenPromise.then((unlisten) => unlisten());
    };
  }, [refetch]);





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
      </div>
    </SettingsCard>
  );
};

export default UserPreferencesCard;

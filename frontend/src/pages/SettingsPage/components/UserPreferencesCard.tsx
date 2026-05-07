import React, { useEffect, useState } from 'react';
import { Cpu, ChevronDown, Zap } from 'lucide-react';

import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

import { useUserPreferences } from '@/hooks/useUserPreferences';
import SettingsCard from './SettingsCard';
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
  const { preferences, updateYoloModelSize, toggleGpuAcceleration } =
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

  const formatTierLabel = (tier: ModelTier) =>
    tier.charAt(0).toUpperCase() + tier.slice(1);

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
                    onClick={() => updateYoloModelSize(tier)}
                  >
                    {formatTierLabel(tier)}
                  </DropdownMenuItem>
                ) : null,
              )}
              {loadingTiers && (
                <DropdownMenuItem disabled>
                  Loading models...
                </DropdownMenuItem>
              )}
              {!loadingTiers && tierFetchError && (
                <DropdownMenuItem disabled>
                  Failed to load models
                </DropdownMenuItem>
              )}
              {!loadingTiers && !tierFetchError && installedTiers.length === 0 && (
                <DropdownMenuItem disabled>
                  No models installed
                </DropdownMenuItem>
              )}
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
              onCheckedChange={() => toggleGpuAcceleration()}
            />
          </div>
        </div>
      </div>
    </SettingsCard>
  );
};

export default UserPreferencesCard;

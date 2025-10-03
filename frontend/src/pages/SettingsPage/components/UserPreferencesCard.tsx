import React from 'react';
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

/**
 * Component for managing user preferences in settings
 */
const UserPreferencesCard: React.FC = () => {
  const { preferences, updatePreference } = useUserPreferences();

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
              <Button variant="outline" className="w-32 justify-between">
                {preferences.YOLO_model_size.charAt(0).toUpperCase() +
                  preferences.YOLO_model_size.slice(1)}
                <ChevronDown className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-32">
              <DropdownMenuItem
                className="cursor-pointer"
                onClick={() =>
                  updatePreference({
                    ...preferences,
                    YOLO_model_size: 'nano',
                  })
                }
              >
                Nano
              </DropdownMenuItem>
              <DropdownMenuItem
                className="cursor-pointer"
                onClick={() =>
                  updatePreference({
                    ...preferences,
                    YOLO_model_size: 'small',
                  })
                }
              >
                Small
              </DropdownMenuItem>
              <DropdownMenuItem
                className="cursor-pointer"
                onClick={() =>
                  updatePreference({
                    ...preferences,
                    YOLO_model_size: 'medium',
                  })
                }
              >
                Medium
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
              onCheckedChange={(checked) =>
                updatePreference({
                  ...preferences,
                  GPU_Acceleration: checked,
                })
              }
            />
          </div>
        </div>
      </div>
    </SettingsCard>
  );
};

export default UserPreferencesCard;

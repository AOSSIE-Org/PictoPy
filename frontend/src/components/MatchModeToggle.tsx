import { cn } from '@/lib/utils';
import { Switch } from '@/components/ui/switch';
import type { FaceMatchMode } from '@/types/Media';

interface MatchModeToggleProps {
  value: FaceMatchMode;
  onChange: (value: FaceMatchMode) => void;
}

/** "Any / All" switch shared by the searches that combine several people. */
export function MatchModeToggle({ value, onChange }: MatchModeToggleProps) {
  return (
    <div className="bg-muted/30 rounded-lg border px-4 py-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Match exact combination</span>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'text-xs transition-colors',
              value === 'match_any'
                ? 'text-foreground font-medium'
                : 'text-muted-foreground',
            )}
          >
            Any
          </span>
          <Switch
            checked={value === 'match_all'}
            onCheckedChange={(checked) =>
              onChange(checked ? 'match_all' : 'match_any')
            }
            aria-label="Toggle match mode between any and all"
          />
          <span
            className={cn(
              'text-xs transition-colors',
              value === 'match_all'
                ? 'text-foreground font-medium'
                : 'text-muted-foreground',
            )}
          >
            All
          </span>
        </div>
      </div>
      <p className="text-muted-foreground mt-1.5 text-xs">
        {value === 'match_any'
          ? 'Photos and videos containing ANY of the selected people'
          : 'Photos and videos containing ALL of the selected people'}
      </p>
    </div>
  );
}

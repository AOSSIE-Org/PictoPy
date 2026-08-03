import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import {
  ArrowDownUp,
  ChevronDown,
  Check,
  Star,
  Calendar,
  type LucideIcon,
} from 'lucide-react';

export interface SortOption<T extends string> {
  value: T;
  label: string;
  icon: LucideIcon;
}

export type GallerySortValue = 'best_match' | 'date';

const GALLERY_SORT_OPTIONS: SortOption<GallerySortValue>[] = [
  { value: 'best_match', label: 'Best match', icon: Star },
  { value: 'date', label: 'Date', icon: Calendar },
];

interface GallerySortDropdownProps<T extends string> {
  value: T;
  onValueChange: (value: T) => void;
  /** Defaults to the gallery's best-match/date pair. */
  options?: SortOption<T>[];
}

export function GallerySortDropdown<T extends string = GallerySortValue>({
  value,
  onValueChange,
  options = GALLERY_SORT_OPTIONS as SortOption<T>[],
}: GallerySortDropdownProps<T>) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          <ArrowDownUp className="mr-2 h-4 w-4" />
          Sort by:
          <ChevronDown className="ml-2 h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {options.map((option) => {
          const Icon = option.icon;
          return (
            <DropdownMenuItem
              key={option.value}
              onSelect={() => onValueChange(option.value)}
            >
              <Icon className="mr-2 h-4 w-4" />
              {option.label}
              <Check
                className={`ml-auto h-4 w-4 ${value === option.value ? 'opacity-100' : 'opacity-0'}`}
              />
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

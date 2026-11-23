import { ChevronDown, Grid2X2, Grid3X3, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useGalleryView } from '@/hooks/useGalleryView';
import { cn } from '@/lib/utils';

export function GalleryViewSelector() {
  const [size, updateSize] = useGalleryView();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="border-border/80 bg-background hover:border-border hover:bg-accent/70 focus-visible:ring-ring/40 focus-visible:ring-offset-background dark:bg-card mr-4 h-9 w-auto gap-2 rounded-xl px-2.5 shadow-none focus-visible:ring-2 focus-visible:ring-offset-2"
          aria-label="Thumbnail size"
          title="Thumbnail size"
        >
          <Grid2X2 aria-hidden="true" className="h-4 w-4" />
          <ChevronDown aria-hidden="true" className="h-3.5 w-3.5 opacity-70" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        sideOffset={8}
        className="border-border/70 w-44 rounded-xl p-1.5 shadow-md"
      >
        {(
          [
            ['small', 'Small', Grid3X3],
            ['medium', 'Medium', Grid2X2],
            ['large', 'Large', Square],
          ] as const
        ).map(([sizeOption, label, Icon]) => (
          <DropdownMenuItem
            key={sizeOption}
            aria-checked={size === sizeOption}
            role="menuitemradio"
            className={cn(
              'focus:bg-accent/80 h-9 gap-2.5 rounded-lg px-2.5',
              size === sizeOption && 'bg-accent/60',
            )}
            onSelect={() => updateSize(sizeOption)}
          >
            <span className="flex h-4 w-4 items-center justify-center">
              {size === sizeOption && (
                <span className="h-1.5 w-1.5 rounded-full bg-current" />
              )}
            </span>
            <Icon className="h-4 w-4" />
            {label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

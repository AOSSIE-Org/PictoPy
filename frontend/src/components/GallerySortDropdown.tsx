import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { ArrowDownUp, ChevronDown, Check, Star, Calendar } from 'lucide-react';

interface GallerySortDropdownProps {
  value: 'best_match' | 'date';
  onValueChange: (value: 'best_match' | 'date') => void;
}

export function GallerySortDropdown({
  value,
  onValueChange,
}: GallerySortDropdownProps) {
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
        <DropdownMenuItem onSelect={() => onValueChange('best_match')}>
          <Star className="mr-2 h-4 w-4" />
          Best match
          <Check
            className={`ml-auto h-4 w-4 ${value === 'best_match' ? 'opacity-100' : 'opacity-0'}`}
          />
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => onValueChange('date')}>
          <Calendar className="mr-2 h-4 w-4" />
          Date
          <Check
            className={`ml-auto h-4 w-4 ${value === 'date' ? 'opacity-100' : 'opacity-0'}`}
          />
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

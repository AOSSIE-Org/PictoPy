import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { X, Filter, Calendar, Tag, Star, MapPin, FileType, HardDrive } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
  setTags,
  setIsFavourite,
  setIsTagged,
  setDateRange,
  setFileSize,
  setFileTypes,
  clearFilters,
  resetFilters,
} from '@/features/filterSlice';
import { RootState } from '@/app/store';

interface AdvancedSearchPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AdvancedSearchPanel({ open, onOpenChange }: AdvancedSearchPanelProps) {
  const dispatch = useDispatch();
  const filters = useSelector((state: RootState) => state.filters);
  const [localTags, setLocalTags] = useState<string>('');

  // Sync localTags with Redux state when panel opens or filters change
  useEffect(() => {
    if (open) {
      setLocalTags(filters.tags.join(', '));
    }
  }, [open, filters.tags]);

  const handleApplyFilters = () => {
    // Always dispatch tags, even if empty (to clear them)
    const tagArray = localTags.trim()
      ? localTags.split(',').map(tag => tag.trim()).filter(Boolean)
      : [];
    dispatch(setTags(tagArray));
    onOpenChange(false);
  };

  const handleClearAll = () => {
    dispatch(clearFilters());
    setLocalTags('');
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-md overflow-y-auto p-0">
        <div className="flex flex-col h-full">
          {/* Header Section */}
          <SheetHeader className="px-6 pt-6 pb-4 border-b">
            <SheetTitle className="flex items-center gap-2 text-lg">
              <Filter className="h-5 w-5" />
              Advanced Search & Filters
            </SheetTitle>
            <SheetDescription className="text-sm mt-1">
              Refine your search with multiple filters
            </SheetDescription>
          </SheetHeader>

          {/* Content Section with padding */}
          <div className="flex-1 overflow-y-auto px-6 py-6">
            <div className="space-y-6">
              {/* Tags Filter */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2 text-sm font-medium">
                  <Tag className="h-4 w-4" />
                  Tags
                </Label>
                <Input
                  placeholder="Enter tags separated by commas (e.g., beach, sunset, family)"
                  value={localTags}
                  onChange={(e) => setLocalTags(e.target.value)}
                  className="w-full"
                />
                {filters.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {filters.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-3 py-1.5 bg-primary/10 text-primary rounded-md text-sm font-medium"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <Separator className="my-6" />

              {/* Favourites Filter */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2 text-sm font-medium">
                  <Star className="h-4 w-4" />
                  Favourites
                </Label>
                <div className="flex gap-3 pt-1">
                  <Button
                    variant={filters.isFavourite === true ? 'default' : 'outline'}
                    size="sm"
                    className="flex-1"
                    onClick={() => dispatch(setIsFavourite(filters.isFavourite === true ? null : true))}
                  >
                    Favourites Only
                  </Button>
                  <Button
                    variant={filters.isFavourite === false ? 'default' : 'outline'}
                    size="sm"
                    className="flex-1"
                    onClick={() => dispatch(setIsFavourite(filters.isFavourite === false ? null : false))}
                  >
                    Exclude Favourites
                  </Button>
                </div>
              </div>

              <Separator className="my-6" />

              {/* Tagged Status Filter */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2 text-sm font-medium">
                  <Tag className="h-4 w-4" />
                  AI Tagged
                </Label>
                <div className="flex items-center justify-between pt-1 px-1">
                  <span className="text-sm text-muted-foreground">
                    Show only AI-tagged images
                  </span>
                  <Switch
                    checked={filters.isTagged === true}
                    onCheckedChange={(checked) => dispatch(setIsTagged(checked ? true : null))}
                  />
                </div>
              </div>

              <Separator className="my-6" />

              {/* Date Range Filter */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2 text-sm font-medium">
                  <Calendar className="h-4 w-4" />
                  Date Range
                </Label>
                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground">From</Label>
                    <Input
                      type="date"
                      value={filters.dateRange.start || ''}
                      onChange={(e) =>
                        dispatch(
                          setDateRange({
                            ...filters.dateRange,
                            start: e.target.value || null,
                          })
                        )
                      }
                      className="w-full"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground">To</Label>
                    <Input
                      type="date"
                      value={filters.dateRange.end || ''}
                      onChange={(e) =>
                        dispatch(
                          setDateRange({
                            ...filters.dateRange,
                            end: e.target.value || null,
                          })
                        )
                      }
                      className="w-full"
                    />
                  </div>
                </div>
              </div>

              <Separator className="my-6" />

              {/* File Size Filter */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2 text-sm font-medium">
                  <HardDrive className="h-4 w-4" />
                  File Size (MB)
                </Label>
                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground">Min</Label>
                    <Input
                      type="number"
                      placeholder="0"
                      value={filters.fileSize.min || ''}
                      onChange={(e) =>
                        dispatch(
                          setFileSize({
                            ...filters.fileSize,
                            min: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        )
                      }
                      className="w-full"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium text-muted-foreground">Max</Label>
                    <Input
                      type="number"
                      placeholder="100"
                      value={filters.fileSize.max || ''}
                      onChange={(e) =>
                        dispatch(
                          setFileSize({
                            ...filters.fileSize,
                            max: e.target.value ? parseFloat(e.target.value) : null,
                          })
                        )
                      }
                      className="w-full"
                    />
                  </div>
                </div>
              </div>

              <Separator className="my-6" />

              {/* File Type Filter */}
              <div className="space-y-3">
                <Label className="flex items-center gap-2 text-sm font-medium">
                  <FileType className="h-4 w-4" />
                  File Type
                </Label>
                <div className="flex flex-wrap gap-2 pt-1">
                  {['image/jpeg', 'image/png', 'image/gif', 'image/webp'].map((type) => (
                    <Button
                      key={type}
                      variant={filters.fileTypes.includes(type) ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => {
                        const newTypes = filters.fileTypes.includes(type)
                          ? filters.fileTypes.filter((t) => t !== type)
                          : [...filters.fileTypes, type];
                        dispatch(setFileTypes(newTypes));
                      }}
                    >
                      {type.split('/')[1].toUpperCase()}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="px-6 py-4 border-t bg-muted/30">
            <div className="flex gap-3">
              <Button onClick={handleClearAll} variant="outline" className="flex-1">
                Clear All
              </Button>
              <Button onClick={handleApplyFilters} className="flex-1">
                Apply Filters
              </Button>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
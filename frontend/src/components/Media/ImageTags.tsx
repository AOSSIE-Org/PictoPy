import { Badge } from '@/components/ui/badge';
import { Tag } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';

interface ImageTagsProps {
  tags: any[];
  showTags?: boolean;
  isImageHovered: boolean;
}

export function ImageTags({
  tags,
  showTags = true,
  isImageHovered,
}: ImageTagsProps) {
  const [isTagsHovered, setIsTagsHovered] = useState(false);
  const [showTagsFromImageHover, setShowTagsFromImageHover] = useState(false);
  const imageHoverTimerRef = useRef<NodeJS.Timeout | null>(null);

  const tagCount = tags.length;

  useEffect(() => {
    if (isImageHovered && !isTagsHovered && tags.length > 0) {
      imageHoverTimerRef.current = setTimeout(() => {
        setShowTagsFromImageHover(true);
      }, 500);
    } else {
      if (imageHoverTimerRef.current) {
        clearTimeout(imageHoverTimerRef.current);
        imageHoverTimerRef.current = null;
      }

      if (!isTagsHovered) {
        setShowTagsFromImageHover(false);
      }
    }

    return () => {
      if (imageHoverTimerRef.current) {
        clearTimeout(imageHoverTimerRef.current);
      }
    };
  }, [isImageHovered, isTagsHovered, tags.length]);

  const shouldShowTags = isTagsHovered || showTagsFromImageHover;

  if (tags.length === 0) {
    return null;
  }

  return (
    <div
      className="absolute bottom-2 left-2 transition-all duration-200"
      onMouseEnter={() => showTags && setIsTagsHovered(true)}
      onMouseLeave={() => showTags && setIsTagsHovered(false)}
    >
      {!shouldShowTags && showTags && (
        <Badge className="flex cursor-pointer items-center gap-1 bg-black/60 text-white hover:bg-black/80">
          <Tag className="h-3 w-3" />
          {tagCount}
        </Badge>
      )}

      {shouldShowTags && showTags && (
        <div className="absolute bottom-0 left-0 z-10 flex max-h-24 max-w-[200px] flex-wrap gap-1 overflow-y-auto rounded-md bg-black/80 p-2 shadow-lg">
          {tags.map((tag: any, index: number) => (
            <Badge
              key={tag.id || index}
              className="border border-white/40 bg-transparent whitespace-nowrap text-white hover:bg-white/10"
            >
              {tag.name || tag}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

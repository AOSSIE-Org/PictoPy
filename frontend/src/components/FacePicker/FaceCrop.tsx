import { cn } from '@/lib/utils';
import type { DetectedFace } from '@/api/api-functions/face_clusters';

interface FaceCropProps {
  src: string;
  face: DetectedFace;
  /** Size of the photo the box is measured in. */
  imageWidth: number;
  imageHeight: number;
  className?: string;
  onError?: () => void;
}

// Show some of the surroundings so the crop reads as a face, not a zoomed blur.
const PADDING = 1.5;

/** A round thumbnail of one face cut out of a larger photo. */
export function FaceCrop({
  src,
  face,
  imageWidth,
  imageHeight,
  className,
  onError,
}: FaceCropProps) {
  const { x, y, width, height } = face.bbox;
  const side = Math.min(
    Math.max(width, height) * PADDING,
    imageWidth,
    imageHeight,
  );
  const left = Math.min(
    Math.max(x + width / 2 - side / 2, 0),
    imageWidth - side,
  );
  const top = Math.min(
    Math.max(y + height / 2 - side / 2, 0),
    imageHeight - side,
  );

  return (
    <span
      className={cn(
        'bg-muted relative inline-block h-10 w-10 shrink-0 overflow-hidden rounded-full',
        className,
      )}
    >
      <img
        src={src}
        alt="Searched face"
        onError={onError}
        draggable={false}
        className="absolute max-w-none"
        style={{
          width: `${(imageWidth / side) * 100}%`,
          left: `${(-left / side) * 100}%`,
          top: `${(-top / side) * 100}%`,
        }}
      />
    </span>
  );
}

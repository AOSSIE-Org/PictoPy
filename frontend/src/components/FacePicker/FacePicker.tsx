import { useState } from 'react';
import { ScanFace } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MatchModeToggle } from '@/components/MatchModeToggle';
import { cn } from '@/lib/utils';
import { MAX_SELECTED_FACES } from '@/utils/faceSearch';
import type { DetectedFace } from '@/api/api-functions/face_clusters';
import type { FaceMatchMode } from '@/types/Media';

interface FacePickerProps {
  imageSrc: string;
  faces: DetectedFace[];
  /** Size of the image the boxes are measured in, not the displayed size. */
  imageWidth: number;
  imageHeight: number;
  facesSkipped: number;
  onSearch: (indices: number[], matchMode: FaceMatchMode) => void;
}

const toPercent = (value: number, total: number) => `${(value / total) * 100}%`;

const centreX = (face: DetectedFace) => face.bbox.x + face.bbox.width / 2;
const centreY = (face: DetectedFace) => face.bbox.y + face.bbox.height / 2;

/** Rows top to bottom, each row left to right, as a person would read it. */
function inReadingOrder(faces: DetectedFace[]): DetectedFace[] {
  const rows: DetectedFace[][] = [];
  for (const face of [...faces].sort((a, b) => centreY(a) - centreY(b))) {
    const row = rows[rows.length - 1];
    // Same row while the face sits within half a face height of the row's first.
    if (
      row &&
      Math.abs(centreY(face) - centreY(row[0])) < row[0].bbox.height / 2
    ) {
      row.push(face);
    } else {
      rows.push([face]);
    }
  }
  return rows.flatMap((row) => row.sort((a, b) => centreX(a) - centreX(b)));
}

/** Lets the user pick which of the faces in a photo to search with. */
export function FacePicker({
  imageSrc,
  faces,
  imageWidth,
  imageHeight,
  facesSkipped,
  onSearch,
}: FacePickerProps) {
  const [selected, setSelected] = useState<number[]>([]);
  const [matchMode, setMatchMode] = useState<FaceMatchMode>('match_any');
  const [imageFailed, setImageFailed] = useState(false);

  const atLimit = selected.length >= MAX_SELECTED_FACES;

  // The detector lists faces by confidence, which looks random on screen, so
  // the numbers on the boxes follow reading order. The backend still gets the
  // detector's own index.
  const labelByIndex = new Map(
    inReadingOrder(faces).map((face, position) => [face.index, position + 1]),
  );

  const toggle = (index: number) =>
    setSelected((previous) =>
      previous.includes(index)
        ? previous.filter((i) => i !== index)
        : previous.length >= MAX_SELECTED_FACES
          ? previous
          : [...previous, index],
    );

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4">
      <div>
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <ScanFace className="h-5 w-5" />
          Who do you want to find?
        </h2>
        <p className="text-muted-foreground text-sm">
          {faces.length} faces were found in this photo. Select one or more to
          search for.
        </p>
      </div>

      {imageFailed ? (
        <p className="text-muted-foreground py-8 text-center text-sm">
          This photo could not be shown.
        </p>
      ) : (
        <div className="relative mx-auto w-fit overflow-hidden rounded-lg border">
          <img
            src={imageSrc}
            alt="Photo to search with"
            draggable={false}
            onError={() => setImageFailed(true)}
            className="block max-h-[60vh] w-auto max-w-full"
          />
          {faces.map((face) => {
            const isSelected = selected.includes(face.index);
            const isBlocked = atLimit && !isSelected;
            return (
              <button
                key={face.index}
                type="button"
                aria-pressed={isSelected}
                aria-label={`Face ${labelByIndex.get(face.index)}`}
                disabled={isBlocked}
                onClick={() => toggle(face.index)}
                style={{
                  left: toPercent(face.bbox.x, imageWidth),
                  top: toPercent(face.bbox.y, imageHeight),
                  width: toPercent(face.bbox.width, imageWidth),
                  height: toPercent(face.bbox.height, imageHeight),
                }}
                className={cn(
                  'absolute rounded-md border-2 transition-colors',
                  'focus-visible:ring-ring focus-visible:ring-2 focus-visible:outline-none',
                  isSelected
                    ? 'border-primary bg-primary/25'
                    : 'hover:border-primary hover:bg-primary/10 border-white/90',
                  isBlocked && 'cursor-not-allowed opacity-40',
                )}
              >
                <span
                  className={cn(
                    'absolute -top-2.5 -left-2.5 flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold',
                    isSelected
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-background text-foreground border',
                  )}
                >
                  {labelByIndex.get(face.index)}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {facesSkipped > 0 && (
        <p className="text-muted-foreground text-xs">
          {facesSkipped === 1
            ? '1 more face was too small or blurry to use.'
            : `${facesSkipped} more faces were too small or blurry to use.`}
        </p>
      )}

      {selected.length >= 2 && (
        <MatchModeToggle value={matchMode} onChange={setMatchMode} />
      )}

      <div className="flex items-center justify-between gap-2">
        <span className="text-muted-foreground text-xs">
          {atLimit
            ? `You can pick up to ${MAX_SELECTED_FACES} faces at a time.`
            : `${selected.length} selected`}
        </span>
        <Button
          disabled={selected.length === 0}
          onClick={() =>
            onSearch(
              [...selected].sort((a, b) => a - b),
              matchMode,
            )
          }
        >
          Search{selected.length > 0 ? ` (${selected.length})` : ''}
        </Button>
      </div>
    </div>
  );
}

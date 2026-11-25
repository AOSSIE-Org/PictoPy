// Intrinsic, not breakpoint-driven: 224px sets the column count and 1fr shares the
// rest, so no resize leaves a ragged gap. Callers add their own padding.
export const MEDIA_GRID_CLASS =
  'grid grid-cols-[repeat(auto-fill,_minmax(224px,_1fr))] gap-4';

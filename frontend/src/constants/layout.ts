// Intrinsic rather than breakpoint-driven: 224px decides the column count and
// the 1fr shares out the remainder, so no resize leaves a ragged trailing gap.
export const MEDIA_GRID_CLASS =
  'grid grid-cols-[repeat(auto-fill,_minmax(224px,_1fr))] gap-4';

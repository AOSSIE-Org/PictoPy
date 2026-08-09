// Intrinsic rather than breakpoint-driven: cards keep a near-constant width and
// the column count follows the window, so resizing reflows instead of stretching.
export const MEDIA_GRID_CLASS =
  'grid grid-cols-[repeat(auto-fill,_minmax(224px,_1fr))] gap-4';

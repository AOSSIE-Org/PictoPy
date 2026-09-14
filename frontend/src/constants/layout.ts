/**
 * The card grid used by every media surface.
 *
 * Intrinsic rather than breakpoint-driven: the cards keep a near-constant
 * width and the column count follows the window, so resizing reflows the
 * grid instead of resizing every card. Callers add their own padding.
 */
export const MEDIA_GRID_CLASS =
  'grid grid-cols-[repeat(auto-fill,_minmax(224px,_1fr))] gap-4';

// layouts.ts
export type LayoutType = "sideBySide" | "grid2x2" | "onePlusThreeSplit";

export interface Placement {
  colStart: number;
  colEnd: number;
  rowStart: number;
  rowEnd: number;
}

export interface LayoutConfig {
  cols: number;
  rows: number;
  placements: Placement[];
  maxImages: number;
}

export const getLayout = (layout: LayoutType): LayoutConfig => {
  switch (layout) {
    case "sideBySide":
      return {
        cols: 2,
        rows: 1,
        maxImages: 2,
        placements: [
          { colStart: 1, colEnd: 2, rowStart: 1, rowEnd: 2 },
          { colStart: 2, colEnd: 3, rowStart: 1, rowEnd: 2 },
        ],
      };

    case "grid2x2":
      return {
        cols: 2,
        rows: 2,
        maxImages: 4,
        placements: [
          { colStart: 1, colEnd: 2, rowStart: 1, rowEnd: 2 },
          { colStart: 2, colEnd: 3, rowStart: 1, rowEnd: 2 },
          { colStart: 1, colEnd: 2, rowStart: 2, rowEnd: 3 },
          { colStart: 2, colEnd: 3, rowStart: 2, rowEnd: 3 },
        ],
      };

    case "onePlusThreeSplit":
      return {
        cols: 3,
        rows: 2,
        maxImages: 4,
        placements: [
          // big top
          { colStart: 1, colEnd: 4, rowStart: 1, rowEnd: 2 },
          { colStart: 1, colEnd: 2, rowStart: 2, rowEnd: 3 },
          { colStart: 2, colEnd: 3, rowStart: 2, rowEnd: 3 },
          { colStart: 3, colEnd: 4, rowStart: 2, rowEnd: 3 },
        ],
      };

    default:
      return { cols: 1, rows: 1, maxImages: 1, placements: [] };
  }
};
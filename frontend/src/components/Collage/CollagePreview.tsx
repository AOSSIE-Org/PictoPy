// CollagePreview.tsx
import React from "react";
import { LayoutType, getLayout } from "./layouts";

interface CollagePreviewProps {
  images: string[];
  layout: LayoutType;
}

const CollagePreview: React.FC<CollagePreviewProps> = ({
  images,
  layout,
}) => {
  const config = getLayout(layout);
  const showImages = images.slice(0, config.maxImages);

  return (
    <div className="w-full h-[420px] rounded-2xl overflow-hidden p-4 bg-white shadow-2xl border border-gray-100">
      <div
        className="grid h-full w-full gap-3"
        style={{
          gridTemplateColumns: `repeat(${config.cols}, 1fr)`,
          gridTemplateRows: `repeat(${config.rows}, 1fr)`,
        }}
      >
        {showImages.map((img, index) => {
          const p = config.placements[index];

          return (
            <div
              key={index}
              style={{
                gridColumn: `${p.colStart} / ${p.colEnd}`,
                gridRow: `${p.rowStart} / ${p.rowEnd}`,
              }}
              className="rounded-lg overflow-hidden bg-white shadow-lg transition duration-300 transform hover:scale-[1.02] hover:shadow-2xl relative"
            >
              <img
                src={img}
                alt="collage-item"
                className="w-full h-full object-cover transition duration-500 filter hover:brightness-105"
              />
              <div className="absolute inset-0 bg-black opacity-10 mix-blend-multiply pointer-events-none"></div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CollagePreview;
import React from "react";
import { LayoutType, getLayout } from "./layouts";

interface CollagePreviewProps {
  images: string[];
  layout: LayoutType;
}

const CollagePreview: React.FC<CollagePreviewProps> = ({ images, layout }) => {
  const config = getLayout(layout);
  const showImages = images.slice(0, Math.min(config.maxImages, config.placements.length));

  return (
    <div className="w-full h-[420px] rounded-xl overflow-hidden p-2 
      bg-white dark:bg-gray-800 
      border border-gray-200 dark:border-gray-700">

      <div
        className="grid h-full w-full gap-2"
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
              className="rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-700"
            >
              <img src={img} className="w-full h-full object-cover" />
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CollagePreview;
